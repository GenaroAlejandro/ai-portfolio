#!/usr/bin/env python3
"""
fetch_kagglehub.py — Download a Kaggle dataset file via kagglehub and place it in ./data/.
Usage:
  python -m src.fetch_kagglehub --dataset redwankarimsony/heart-disease-data \
                                --file heart_disease_uci.csv \
                                --name heart_disease.csv
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import kagglehub

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, help="kagglehub dataset slug")
    ap.add_argument("--file", required=True, help="filename inside dataset")
    ap.add_argument("--name", default=None, help="output name (default: same as --file)")
    ap.add_argument("--force", action="store_true", help="overwrite if exists")
    args = ap.parse_args()

    print(f"[INFO] Downloading dataset with kagglehub: {args.dataset}")
    ds_path = Path(kagglehub.dataset_download(args.dataset))

    src = ds_path / args.file
    if not src.exists():
        raise SystemExit(f"[ERROR] File not found in dataset cache: {src}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / (args.name or args.file)
    if out.exists() and not args.force:
        print(f"[SKIP] {out} exists (use --force to overwrite)")
        return

    shutil.copy2(src, out)
    print(f"[OK] Saved: {out}")

if __name__ == "__main__":
    main()


"""
python -m src.fetch_kagglehub --dataset redwankarimsony/heart-disease-data --file heart_disease_uci.csv --name heart_disease.csv
"""