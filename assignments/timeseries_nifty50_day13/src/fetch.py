#!/usr/bin/env python3
"""
../src/fetch.py — Consistent three-mode dataset fetcher for Day 13 (NIFTY50).

Choose ONE mode (mutually exclusive):
  1) --nifty            : Download the NIFTY50 dataset (Kaggle *dataset* ashishjangra27/nifty-50-25-yrs-data).
  2) --url <link> ...   : Download one or more HTTP/HTTPS URLs (CSV/ZIP/etc.).
  3) --kaggle <slug>    : Download Kaggle data.
                           - If <slug> contains a slash ("owner/name"), use Kaggle *datasets download*.
                           - Otherwise, treat it as a *competition* and use Kaggle *competitions download*.

Common options:
  --dest <folder>       : Output directory (default: ../data)
  --force               : Overwrite files if they already exist

Examples:
  # 1) Default NIFTY50 dataset (Day 13)
  python ../src/fetch.py --nifty --dest ../data

  # 2) One or more URLs
  python ../src/fetch.py --url https://example.com/a.csv --url https://example.com/b.zip --dest ../data

  # 3) Kaggle (auto-detect dataset vs competition)
  #    Dataset (owner/name):
  python ../src/fetch.py --kaggle ashishjangra27/nifty-50-25-yrs-data --dest ../data
  #    Competition (slug only):
  python ../src/fetch.py --kaggle store-sales-time-series-forecasting --dest ../data
"""

from __future__ import annotations
import argparse, subprocess, sys, zipfile, os, shutil
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlsplit

DEFAULT_DEST = "../data"
NIFTY_DATASET = "ashishjangra27/nifty-50-25-yrs-data"  # Kaggle dataset owner/name


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def download_url(url: str, dest: Path, force: bool = False) -> Path:
    """Stream a URL to disk. Keeps the original filename from the URL."""
    ensure_dir(dest)
    name = Path(urlsplit(url).path).name or "downloaded.file"
    out = dest / name
    if out.exists() and not force:
        print(f"[SKIP] {out} exists (use --force to overwrite)")
        return out
    print(f"[GET ] {url}[SAVE] {out}")
    with urlopen(url) as r, open(out, "wb") as f:
        while True:
            chunk = r.read(8192)
            if not chunk:
                break
            f.write(chunk)
    if out.stat().st_size == 0:
        raise SystemExit(f"[ERROR] Empty file: {out}")
    return out


def unzip_if_zip(path: Path, dest: Path) -> None:
    """Unzip if the file is a .zip archive."""
    if path.suffix.lower() == ".zip" and path.exists():
        print(f"[UNZIP] {path} -> {dest}")
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(dest)


def _run_kaggle(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        raise SystemExit("[ERROR] Kaggle CLI not found. Install with 'pip install kaggle' and set up ~/.kaggle/kaggle.json")


def kaggle_download(slug: str, dest: Path) -> None:
    """Download from Kaggle; auto-detect *datasets* vs *competitions* based on the slug.
    - If slug contains '/', assume datasets: `kaggle datasets download -d owner/name -p dest`
    - Else, assume competition: `kaggle competitions download -c slug -p dest`
    After download, unzip any zip archives found in dest.
    """
    ensure_dir(dest)
    if "/" in slug:
        cmd = ["kaggle", "datasets", "download", "-d", slug, "-p", str(dest)]
    else:
        cmd = ["kaggle", "competitions", "download", "-c", slug, "-p", str(dest)]
    print("[KAGGLE]", " ".join(cmd))
    _run_kaggle(cmd)
    # unzip any archives we got
    for z in dest.glob("*.zip"):
        unzip_if_zip(z, dest)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Consistent three-mode fetcher (nifty | url | kaggle)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--nifty", action="store_true", help="Fetch the Day 13 NIFTY50 dataset (Kaggle dataset)")
    g.add_argument("--kaggle", metavar="SLUG", help="Kaggle slug (owner/name for datasets OR slug for competition)")
    g.add_argument("--url", action="append", help="HTTP/HTTPS URL to download (can be repeated)")
    p.add_argument("--dest", default=DEFAULT_DEST, help=f"Output folder (default: {DEFAULT_DEST})")
    p.add_argument("--force", action="store_true", help="Overwrite existing files")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    dest = Path(args.dest)

    if args.nifty:
        # Equivalent to: kaggle datasets download -d ashishjangra27/nifty-50-25-yrs-data
        kaggle_download(NIFTY_DATASET, dest)
        print("[DONE]")
        return 0

    if args.kaggle:
        kaggle_download(args.kaggle, dest)
        print("[DONE]")
        return 0

    if args.url:
        for link in args.url:
            out = download_url(link, dest, force=args.force)
            unzip_if_zip(out, dest)
        print("[DONE]")
        return 0

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
