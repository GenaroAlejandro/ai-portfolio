#!/usr/bin/env python3
"""
fetch.py — Unified downloader (backward-compatible).

Original behavior (kept):
  - Fetch a single file via:
      --path <repo-path under GFG_BASE>   (builds a RAW URL)
      --url  <full RAW url>

New capabilities (mutually exclusive with the above):
  - --kaggle-dataset "<owner/dataset>" [--dest ../data/celeba] [--unzip] [--force]
  - --github-file    "<owner/repo>" --repo-path "<path/in/repo>" [--ref main] [--dest ../data]
  - --github-asset   "<owner/repo>" --tag "<vX.Y.Z>" --asset-name "<file>" [--dest ../data]
  - --tfds-export    "<dataset:ver>" --split train|validation|test [--dest ../data/export] [--limit 0]

Default destination remains ../data/ (relative to this script) unless overridden.
"""

import argparse
import os
import sys
from pathlib import Path
from urllib.request import urlretrieve
from urllib.parse import urlparse

# ---------- CONSTANTS ----------
GFG_BASE = "https://raw.githubusercontent.com/GeeksforGeeksDS/21-Days-21-Projects-Dataset/main/"

# ---------- HELPERS ----------
def here() -> Path:
    return Path(__file__).resolve().parent

def default_data_dir() -> Path:
    # Preserve your original behavior: ../data relative to this script
    return (here() / ".." / "data").resolve()

def raw_from_path(path: str) -> str:
    return f"{GFG_BASE.rstrip('/')}/{path.lstrip('/')}"

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def human(n: int) -> str:
    for u in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"

def download_stream(url: str, dest: Path, headers=None) -> Path:
    # Streamed download (for large assets); falls back to urllib if requests missing.
    try:
        import requests
        ensure_dir(dest.parent)
        with requests.get(url, stream=True, headers=headers or {}, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            tmp = dest.with_suffix(dest.suffix + ".part")
            done = 0
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        bar = int(50 * done / max(total, 1))
                        sys.stdout.write("\r[{}{}] {}/{}".format(
                            "=" * bar, " " * (50 - bar), human(done), human(total)))
                        sys.stdout.flush()
        sys.stdout.write("\n")
        tmp.replace(dest)
        return dest
    except ImportError:
        # Minimal dependency path (original behavior)
        urlretrieve(url, dest)
        return dest

# ---------- ORIGINAL MODE ----------
def fetch_one_file(path: str = None, url: str = None, name: str = None,
                   force: bool = False, dest: Path = None) -> Path:
    if not url and not path:
        raise ValueError("Either --url or --path must be provided for single-file mode.")
    if not dest:
        dest = default_data_dir()

    final_url = url or raw_from_path(path)
    basename_source = url or path
    filename = name or os.path.basename(urlparse(basename_source).path)

    out_path = (dest / filename).resolve()
    if out_path.exists() and not force:
        print(f"[SKIP] {out_path} exists (use --force to overwrite)")
        return out_path

    ensure_dir(dest)
    print(f"[GET ] {final_url}")
    print(f"[SAVE] {out_path}")
    download_stream(final_url, out_path)
    print("[DONE]")
    return out_path

# ---------- NEW MODES ----------
def fetch_kaggle_dataset(dataset: str, dest: Path, unzip: bool, force: bool) -> None:
    from shutil import which
    if which("kaggle") is None:
        print("ERROR: kaggle CLI not found. Install with: pip install kaggle", file=sys.stderr)
        sys.exit(1)
    ensure_dir(dest)
    if any(dest.iterdir()) and not force:
        print(f"[SKIP] '{dest}' is not empty (use --force to re-download).")
        return
    import subprocess
    cmd = ["kaggle", "datasets", "download", "-d", dataset, "-p", str(dest)]
    if unzip:
        cmd.append("--unzip")
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)
    print("[DONE] Kaggle download")

def fetch_github_file(repo: str, repo_path: str, ref: str, dest: Path) -> Path:
    # e.g., repo="owner/name", repo_path="weights/generator_700.h5"
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{repo_path.lstrip('/')}"
    out = (dest / Path(repo_path).name).resolve()
    ensure_dir(dest)
    print(f"[GET ] {url}")
    print(f"[SAVE] {out}")
    download_stream(url, out)
    print("[DONE]")
    return out

def fetch_github_asset(repo: str, tag: str, asset_name: str, dest: Path) -> Path:
    # Requires requests; uses public API (token optional via env GITHUB_TOKEN).
    import requests, os
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    api = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    print(f"[INFO] Querying release: {api}")
    r = requests.get(api, headers=headers, timeout=60)
    r.raise_for_status()
    rel = r.json()
    assets = rel.get("assets", [])
    asset = next((a for a in assets if a.get("name") == asset_name), None)
    if not asset:
        raise SystemExit(f"Asset '{asset_name}' not found in release '{tag}'.")
    url = asset["browser_download_url"]
    out = (dest / asset_name).resolve()
    ensure_dir(dest)
    print(f"[GET ] {url}")
    print(f"[SAVE] {out}")
    download_stream(url, out)
    print("[DONE]")
    return out

def tfds_export(dataset: str, split: str, dest: Path, limit: int) -> None:
    ensure_dir(dest)
    import tensorflow_datasets as tfds
    import imageio.v2 as imageio
    import numpy as np
    print(f"[INFO] Loading TFDS: {dataset} split={split}")
    ds, _ = tfds.load(dataset, split=split, as_supervised=True, with_info=True)
    n = 0
    for img, _ in tfds.as_numpy(ds):
        # img is uint8 HxWxC; write PNG
        out = (dest / f"{split}_{n:06d}.png").resolve()
        imageio.imwrite(out, img)
        n += 1
        if limit and n >= limit:
            break
        if n % 200 == 0:
            print(f"[INFO] Exported {n} images...")
    print(f"[DONE] Exported {n} images to {dest}")

def fetch_github_repo(repo: str, branch: str, dest: Path, unzip: bool) -> Path:
    """
    Download a full GitHub repository as ZIP (default branch = main).
    Example: repo='AshishJangra27/Face-Generator-with-GAN'
    """
    url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
    filename = f"{repo.replace('/', '_')}_{branch}.zip"
    out_zip = dest / filename
    ensure_dir(dest)
    print(f"[GET ] {url}")
    print(f"[SAVE] {out_zip}")
    download_stream(url, out_zip)
    if unzip:
        import zipfile
        with zipfile.ZipFile(out_zip, "r") as z:
            z.extractall(dest)
        print(f"[UNZIP] Extracted to {dest}")
    print("[DONE]")
    return out_zip


# ---------- CLI ----------
def main():
    p = argparse.ArgumentParser(description="Fetch utility (single-file + Kaggle/GitHub/TFDS).")
    g = p.add_mutually_exclusive_group(required=True)

    # Original single-file mode (compat)
    g.add_argument("--path", help="Repo path under GFG_BASE (e.g., Datasets/Face-Generator-with-GAN)")
    g.add_argument("--url", help="Full RAW URL (e.g., https://.../file.csv)")

    # New modes
    g.add_argument("--kaggle-dataset", help='Kaggle dataset, e.g. "jessicali9530/celeba-dataset"')
    g.add_argument("--github-file", help='GitHub repo "owner/name" for raw file download')
    g.add_argument("--github-asset", help='GitHub repo "owner/name" for release asset download')
    g.add_argument("--tfds-export", help='TFDS dataset "name:version", e.g., "oxford_flowers102:2.1.1"')

    # Shared/compat options
    p.add_argument("--name", help="Rename output file (single-file mode only)")
    p.add_argument("--force", action="store_true", help="Overwrite or redownload if exists")
    p.add_argument("--dest", default=str(default_data_dir()), help="Destination directory (default: ../data/)")

    # Extra args for new modes
    p.add_argument("--unzip", action="store_true", help="Unzip (Kaggle)")
    p.add_argument("--repo-path", help="Path in repo (GitHub raw file)")
    p.add_argument("--ref", default="main", help="Git branch/tag for GitHub raw (default: main)")
    p.add_argument("--tag", help="GitHub release tag (for --github-asset)")
    p.add_argument("--asset-name", help="Exact asset file name (for --github-asset)")
    p.add_argument("--split", choices=["train","validation","test"], default="train", help="TFDS split")
    p.add_argument("--limit", type=int, default=0, help="TFDS export limit (0 = all)")


    g.add_argument("--github-repo", help='GitHub repo "owner/name" for full ZIP download')
    p.add_argument("--branch", default="main", help="Branch to download for --github-repo")

    args = p.parse_args()
    dest = Path(args.dest).resolve()

    # Dispatch
    if args.kaggle_dataset:
        fetch_kaggle_dataset(args.kaggle_dataset, dest, unzip=args.unzip, force=args.force)

    elif args.github_file:
        if not args.repo_path:
            p.error("--github-file requires --repo-path")
        fetch_github_file(args.github_file, args.repo_path, args.ref, dest)

    elif args.github_asset:
        if not args.tag or not args.asset_name:
            p.error("--github-asset requires --tag and --asset-name")
        fetch_github_asset(args.github_asset, args.tag, args.asset_name, dest)

    elif args.tfds_export:
        tfds_export(args.tfds_export, args.split, dest, args.limit)

    elif args.github_repo:
        fetch_github_repo(args.github_repo, args.branch, dest, unzip=args.unzip)

    else:
        # Original single-file mode
        fetch_one_file(path=args.path, url=args.url, name=args.name, force=args.force, dest=dest)

if __name__ == "__main__":
    main()
