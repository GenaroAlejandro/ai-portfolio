#!/usr/bin/env python3
"""
fetch.py — Tiny, focused dataset fetcher for Day 6.

Choose ONE mode:
  1) --airline        : Download the classic airline passengers CSV from the GfG repo.
  2) --url <link> ... : Download one or more HTTP/HTTPS URLs (CSV/ZIP/etc.).
  3) --kaggle <slug>  : Download a FULL Kaggle competition archive (requires kaggle CLI).

Common options:
  --dest <folder>     : Output directory (default: data)
  --force             : Overwrite files if they already exist

Examples:
  # 1) Quick start (airline dataset)
  python src/fetch.py --airline --dest data

  # 2) One or more URLs
  python src/fetch.py --url https://example.com/a.csv --url https://example.com/b.zip --dest data

  # 3) Full Kaggle competition (then auto-unzip)
  python src/fetch.py --kaggle store-sales-time-series-forecasting --dest data
"""

from __future__ import annotations
import argparse, subprocess, sys, zipfile, os
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlsplit

# Single default dataset (keeps notebooks simple)
AIRLINE_URL = (
    "https://raw.githubusercontent.com/GeeksforGeeksDS/21-Days-21-Projects-Dataset/"
    "main/Datasets/airline_passenger_timeseries.csv"
)

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def download_url(url: str, dest: Path, force: bool=False) -> Path:
    """Stream a URL to disk. Keeps the original filename from the URL."""
    ensure_dir(dest)
    name = Path(urlsplit(url).path).name or "downloaded.file"
    out = dest / name
    if out.exists() and not force:
        print(f"[SKIP] {out} exists (use --force to overwrite)")
        return out
    print(f"[GET ] {url}\n[SAVE] {out}")
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

def kaggle_download_full(slug: str, dest: Path) -> None:
    """Run 'kaggle competitions download' and unzip all zips."""
    ensure_dir(dest)
    cmd = ["kaggle", "competitions", "download", "-c", slug, "-p", str(dest)]
    print("[KAGGLE]", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        raise SystemExit("[ERROR] Kaggle CLI not found. Install with 'pip install kaggle' and set up ~/.kaggle/kaggle.json")
    # unzip any archives we got
    for z in dest.glob("*.zip"):
        unzip_if_zip(z, dest)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Minimal dataset fetcher (three simple modes)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--airline", action="store_true", help="Fetch the airline passengers CSV")
    g.add_argument("--kaggle", metavar="SLUG", help="Download FULL Kaggle competition archive")
    g.add_argument("--url", action="append", help="HTTP/HTTPS URL to download (can be repeated)")
    p.add_argument("--dest", default="data", help="Output folder (default: data)")
    p.add_argument("--force", action="store_true", help="Overwrite existing files")
    return p.parse_args()

def main() -> int:
    args = parse_args()
    dest = Path(args.dest)

    if args.airline:
        out = download_url(AIRLINE_URL, dest, force=args.force)
        unzip_if_zip(out, dest)
        print("[DONE]"); return 0

    if args.kaggle:
        kaggle_download_full(args.kaggle, dest)
        print("[DONE]"); return 0

    if args.url:
        for link in args.url:
            out = download_url(link, dest, force=args.force)
            unzip_if_zip(out, dest)
        print("[DONE]"); return 0

    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
