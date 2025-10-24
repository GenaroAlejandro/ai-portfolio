#!/usr/bin/env python3
"""
fetch.py — Single-purpose downloader for ONE dataset file into this assignment's data/ folder.

It supports three *mutually exclusive* ways to fetch a file:

  1) --path        : A file path inside the GeeksforGeeks 21-Days-21-Projects dataset repo.
                     (We construct the RAW GitHub URL for you.)

  2) --url         : Any fully-qualified RAW URL you trust (e.g., GitHub raw CSV).

  3) --from-kaggle : Download a file (e.g., train.csv) from a Kaggle *competition* using the Kaggle CLI.

Typical usage for Kaggle House Prices (recommended for this project):
  python assignments/housing_trends_day3/src/fetch.py \
    --from-kaggle \
    --competition house-prices-advanced-regression-techniques \
    --file train.csv \
    --name housing.csv
"""

import argparse
import os
import shutil
import subprocess
import tempfile
import zipfile
from urllib.request import urlretrieve              # Simple downloader for URLs
from urllib.parse import urlparse                   # Helps derive filename from a URL
from pathlib import Path

# ---- 1) CONSTANTS -------------------------------------------------------------

# Base RAW URL for the GeeksforGeeks datasets repo. If that repo moves, update this.
GFG_BASE = "https://raw.githubusercontent.com/GeeksforGeeksDS/21-Days-21-Projects-Dataset/main/"


# ---- 2) HELPERS ---------------------------------------------------------------

def raw_from_path(path: str) -> str:
    """
    Convert a repo-relative path like 'Datasets/netflix_titles.csv'
    into a full RAW GitHub URL.
    """
    return f"{GFG_BASE.rstrip('/')}/{path.lstrip('/')}"

def ensure_dir(p: Path) -> None:
    """Create directory p (and parents) if it doesn't exist."""
    p.mkdir(parents=True, exist_ok=True)

def copy_kaggle_json_if_provided(kaggle_json: str) -> None:
    """
    If the user passed --kaggle-json <path>, copy their token to ~/.kaggle/kaggle.json
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
    """
    Verify that the 'kaggle' CLI is available on PATH.
    The CLI ships via pip/conda; ensure your environment has it.
    """
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
        # Retrieve just one file from the competition into tmpdir
        cmd = ["kaggle", "competitions", "download", "-c", competition, "-f", file_name, "-p", str(tmpdir)]
        subprocess.run(cmd, check=True)

        zipped = tmpdir / f"{file_name}.zip"  # Kaggle often returns <file>.csv.zip
        candidate = tmpdir / file_name        # This is what we want after unzip

        # If we got a zip, extract it
        if zipped.exists():
            with zipfile.ZipFile(zipped, "r") as zf:
                zf.extractall(tmpdir)

        # Validate that the target file exists now
        if not candidate.exists():
            raise SystemExit(f"[ERROR] Expected file not found after download: {candidate}")

        # Copy to the final destination
        shutil.copy2(candidate, out_path)
        print(f"[OK] Saved to {out_path}")
    finally:
        # For debugging you can leave tmpdir; otherwise uncomment to cleanup.
        # shutil.rmtree(tmpdir, ignore_errors=True)
        pass


# ---- 3) MAIN CLI --------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch ONE dataset file into ../data/")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--path", help="Path inside the GfG repo (e.g., Datasets/netflix_titles.csv)")
    group.add_argument("--url", help="Full RAW URL (e.g., https://raw.githubusercontent.com/.../file.csv)")
    group.add_argument("--from-kaggle", action="store_true", help="Use Kaggle CLI to download from a competition")

    parser.add_argument("--name", help="Rename the output file (default: source basename)")
    parser.add_argument("--force", action="store_true", help="Overwrite if the file already exists")

    # Kaggle-specific options
    parser.add_argument("--competition", default="house-prices-advanced-regression-techniques",
                        help="Kaggle competition slug (default: house-prices-advanced-regression-techniques)")
    parser.add_argument("--file", default="train.csv",
                        help="Filename to pull from the competition (default: train.csv)")
    parser.add_argument("--kaggle-json",
                        help="Path to your kaggle.json; if provided, it will be copied to ~/.kaggle/kaggle.json")

    args = parser.parse_args()

    # Resolve the standard output folder: assignments/<assignment>/data/
    out_dir = Path(__file__).resolve().parents[1] / "data"
    ensure_dir(out_dir)

    # --- Kaggle mode ---
    if args.from_kaggle:
        # 1) Put token in place if user passed --kaggle-json
        copy_kaggle_json_if_provided(args.kaggle_json)
        # 2) Ensure the 'kaggle' CLI is found
        ensure_kaggle_cli()
        # 3) Decide the final filename saved to data/
        final_name = args.name or args.file
        out_path = out_dir / final_name
        if out_path.exists() and not args.force:
            print(f"[SKIP] {out_path} exists (use --force to overwrite)")
            return
        # 4) Download and unzip to out_path
        download_from_kaggle_competition(args.competition, args.file, out_path)
        print("[DONE]")
        return

    # --- URL or GfG path modes ---
    # Build the source URL
    url = args.url or raw_from_path(args.path)
    # Derive output filename: either --name or the basename of the URL/path
    basename_source = args.url or args.path
    final_name = args.name or os.path.basename(urlparse(basename_source).path)
    out_path = out_dir / final_name

    if out_path.exists() and not args.force:
        print(f"[SKIP] {out_path} exists (use --force to overwrite)")
        return

    print(f"[GET ] {url}")
    print(f"[SAVE] {out_path}")
    urlretrieve(url, out_path)
    print("[DONE]")


if __name__ == "__main__":
    main()