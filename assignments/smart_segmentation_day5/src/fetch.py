#!/usr/bin/env python3
"""
fetch.py — Single-purpose downloader for ONE dataset file into this project's data/ folder.

Project layout (assumed):
ai-portfolio/
  smart_segmentation/
    data/              <-- this script writes here by default
    notebooks/
    src/
    models/ (optional)
    reports/ (optional)

It supports three *mutually exclusive* ways to fetch a file:

  1) --path        : A file path inside the GeeksforGeeks 21-Days-21-Projects dataset repo.
                     (We construct the RAW GitHub URL for you.)
                     Example: --path Datasets/Mall_Customers.csv

  2) --url         : Any fully-qualified RAW URL you trust (e.g., GitHub raw CSV).

  3) --from-kaggle : Download a file (e.g., train.csv) from a Kaggle *competition* using the Kaggle CLI.

You can optionally override the output directory:
  --outdir smart_segmentation/data

Typical usage for this Day 5 project (recommended):
  python smart_segmentation/src/fetch.py \
    --path Datasets/Mall_Customers.csv \
    --name customers.csv

Example (URL form):
  python smart_segmentation/src/fetch.py \
    --url https://raw.githubusercontent.com/GeeksforGeeksDS/21-Days-21-Projects-Dataset/main/Datasets/Mall_Customers.csv \
    --name customers.csv
"""

import argparse
import os
import shutil
import subprocess
import tempfile
import zipfile
from urllib.request import urlretrieve
from urllib.parse import urlparse
from pathlib import Path
import sys

# ---- 1) CONSTANTS -------------------------------------------------------------

# Base RAW URL for the GeeksforGeeks datasets repo. If that repo moves, update this.
GFG_BASE = "https://raw.githubusercontent.com/GeeksforGeeksDS/21-Days-21-Projects-Dataset/main/"

# ---- 2) HELPERS ---------------------------------------------------------------

def raw_from_path(path: str) -> str:
    """Convert a repo-relative path like 'Datasets/Mall_Customers.csv' into a full RAW GitHub URL."""
    return f"{GFG_BASE.rstrip('/')}/{path.lstrip('/')}"

def ensure_dir(p: Path) -> None:
    """Create directory p (and parents) if it doesn't exist."""
    p.mkdir(parents=True, exist_ok=True)

def copy_kaggle_json_if_provided(kaggle_json: str) -> None:
    """
    If the user passed --kaggle-json <path>, copy token to ~/.kaggle/kaggle.json
    and set proper permissions (POSIX). On Windows, chmod is not strictly required.
    """
    if not kaggle_json:
        return
    src = Path(kaggle_json).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"[ERROR] Provided --kaggle-json not found: {src}")
    dst = Path.home() / ".kaggle" / "kaggle.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    try:
        os.chmod(dst, 0o600)  # Linux/Mac; safe to ignore errors on Windows
    except Exception:
        pass
    print(f"[INFO] Copied Kaggle token to: {dst}")

def ensure_kaggle_cli() -> None:
    """Verify that the 'kaggle' CLI is available on PATH."""
    try:
        subprocess.run(
            ["kaggle", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except Exception as e:
        raise SystemExit(
            "[ERROR] 'kaggle' CLI not found. Install it (conda-forge or pip) and ensure it's on PATH."
        ) from e

def download_from_kaggle_competition(competition: str, file_name: str, out_path: Path) -> None:
    """
    Download a *single file* from a Kaggle competition using the Kaggle CLI.
    Kaggle usually zips the requested file; this function unzips it if needed
    and copies the final CSV to 'out_path'.
    """
    ensure_dir(out_path.parent)
    tmpdir = Path(tempfile.mkdtemp(prefix="kaggle_dl_"))
    try:
        print(f"[INFO] Downloading from Kaggle: comp='{competition}', file='{file_name}'")
        cmd = ["kaggle", "competitions", "download", "-c", competition, "-f", file_name, "-p", str(tmpdir)]
        subprocess.run(cmd, check=True)

        zipped = tmpdir / f"{file_name}.zip"   # often returns <file>.csv.zip
        candidate = tmpdir / file_name         # expected unzipped filename

        # If we got a zip, extract it
        if zipped.exists():
            with zipfile.ZipFile(zipped, "r") as zf:
                zf.extractall(tmpdir)

        if not candidate.exists():
            # Some competitions may deliver different casing or paths; try best-effort scan
            matches = list(tmpdir.glob("**/*"))
            hint = "\n".join(f" - {m.name}" for m in matches[:10])
            raise SystemExit(
                f"[ERROR] Expected file not found after download: {candidate}\n"
                f"Files in temp dir:\n{hint}"
            )

        shutil.copy2(candidate, out_path)
        print(f"[OK] Saved to {out_path}")
    finally:
        # Clean temp dir
        shutil.rmtree(tmpdir, ignore_errors=True)

def resolve_default_outdir(script_file: Path) -> Path:
    """
    Default to <project_root>/data where project_root is the parent of src/.
    Example: smart_segmentation/src/fetch.py -> smart_segmentation/data
    """
    # .../smart_segmentation/src/fetch.py -> parents[1] is .../smart_segmentation
    project_root = script_file.parent.parent
    return project_root / "data"

# ---- 3) MAIN CLI --------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch ONE dataset file into this project's data/ folder.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", help="Path inside the GfG repo (e.g., Datasets/Mall_Customers.csv)")
    group.add_argument("--url", help="Full RAW URL (e.g., https://raw.githubusercontent.com/.../file.csv)")
    group.add_argument("--from-kaggle", action="store_true", help="Use Kaggle CLI to download from a competition")

    parser.add_argument("--name", help="Rename the output file (default: source basename)")
    parser.add_argument("--force", action="store_true", help="Overwrite if the file already exists")
    parser.add_argument("--outdir", help="Override output dir (default: <project>/data)")

    # Kaggle-specific options
    parser.add_argument("--competition", default="house-prices-advanced-regression-techniques",
                        help="Kaggle competition slug (default: house-prices-advanced-regression-techniques)")
    parser.add_argument("--file", default="train.csv",
                        help="Filename to pull from the competition (default: train.csv)")
    parser.add_argument("--kaggle-json",
                        help="Path to your kaggle.json; if provided, it will be copied to ~/.kaggle/kaggle.json")

    args = parser.parse_args()

    # Resolve output folder
    script_path = Path(__file__).resolve()
    out_dir = Path(args.outdir).resolve() if args.outdir else resolve_default_outdir(script_path)
    ensure_dir(out_dir)

    # --- Kaggle mode ---
    if args.from_kaggle:
        copy_kaggle_json_if_provided(args.kaggle_json)
        ensure_kaggle_cli()
        final_name = args.name or args.file
        out_path = out_dir / final_name
        if out_path.exists() and not args.force:
            print(f"[SKIP] {out_path} exists (use --force to overwrite)")
            return
        download_from_kaggle_competition(args.competition, args.file, out_path)
        print("[DONE]")
        return

    # --- URL or GfG path modes ---
    url = args.url or raw_from_path(args.path)
    basename_source = args.url or args.path
    final_name = args.name or os.path.basename(urlparse(basename_source).path)
    out_path = out_dir / final_name

    if out_path.exists() and not args.force:
        print(f"[SKIP] {out_path} exists (use --force to overwrite)")
        return

    print(f"[GET ] {url}")
    print(f"[SAVE] {out_path}")
    try:
        ensure_dir(out_path.parent)
        urlretrieve(url, out_path)
    except Exception as e:
        raise SystemExit(f"[ERROR] Failed to download:\n  URL: {url}\n  REASON: {e}") from e

    # Quick sanity check for empty file
    try:
        if out_path.stat().st_size == 0:
            raise SystemExit(f"[ERROR] Downloaded file is empty: {out_path}")
    except FileNotFoundError:
        raise SystemExit(f"[ERROR] File not found after download: {out_path}")

    print("[DONE]")

if __name__ == "__main__":
    # Make Ctrl+C exit cleanly on Windows/Unix
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
