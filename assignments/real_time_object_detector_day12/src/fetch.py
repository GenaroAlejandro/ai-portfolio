"""
Download and extract CelebA (img_align_celeba) via Kaggle CLI.

Requirements:
  - environment.yml includes 'kaggle' (pip)
  - Kaggle API credentials present either as:
      Windows:  %USERPROFILE%\.kaggle\kaggle.json
      Linux/WSL: ~/.kaggle/kaggle.json
    Get it from https://www.kaggle.com/settings/account (Create New API Token)

It will extract into:
  assignments/day12_real_time_object_detector/data/celeba/img_align_celeba/
"""

import os
import subprocess
import zipfile
from pathlib import Path

DATASET = "jessicali9530/celeba-dataset"
ROOT = Path(__file__).resolve().parents[0]
DATA_DIR = ROOT / "data" / "celeba"
ZIP_DIR = DATA_DIR / "zips"
OUT_DIR = DATA_DIR / "img_align_celeba"

def run(cmd):
    print(">>", " ".join(cmd))
    subprocess.check_call(cmd, shell=(os.name == "nt"))

def ensure_kaggle_creds():
    home = Path.home()
    cred = home / ".kaggle" / "kaggle.json"
    if not cred.exists():
        raise RuntimeError(
            f"Kaggle credentials not found at {cred}. "
            "Download kaggle.json from Kaggle > Account > Create API Token, "
            "then place it there and set permissions (chmod 600 on Linux/WSL)."
        )

def main():
    ensure_kaggle_creds()
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Download dataset (will drop multiple zips incl. img_align_celeba.zip)
    run(["kaggle", "datasets", "download", "-d", DATASET, "-p", str(ZIP_DIR), "-o"])

    # Find and extract target zip
    target_zip = None
    for z in ZIP_DIR.glob("*.zip"):
        if "img_align_celeba" in z.name:
            target_zip = z
            break

    if target_zip is None:
        # Fallback: extract everything, then locate folder
        for z in ZIP_DIR.glob("*.zip"):
            print(f"Extracting {z.name} ...")
            with zipfile.ZipFile(z, "r") as f:
                f.extractall(DATA_DIR)
    else:
        print(f"Extracting {target_zip.name} ...")
        with zipfile.ZipFile(target_zip, "r") as f:
            f.extractall(DATA_DIR)

    # Normalize output path name (some mirrors unpack into different casing)
    candidates = [
        DATA_DIR / "img_align_celeba",
        DATA_DIR / "img_align_celeba_png",
        DATA_DIR / "img_align_celeba_jpg",
    ]
    found = None
    for c in candidates:
        if c.exists():
            found = c
            break

    if not found:
        # Try to find a folder with many jpgs as last resort
        for p in DATA_DIR.rglob("*"):
            if p.is_dir() and any(suffix in {".jpg", ".jpeg", ".png"} for suffix in (".jpg", ".jpeg", ".png")):
                # Skip; rglob above won’t check files. So do a quick content peek:
                imgs = list(p.glob("*.jpg")) + list(p.glob("*.png")) + list(p.glob("*.jpeg"))
                if len(imgs) > 10000:  # CelebA has 200k
                    found = p
                    break

    if not found:
        print("WARNING: Could not locate 'img_align_celeba' folder automatically.")
        print(f"Please inspect {DATA_DIR} and update your notebook path accordingly.")
    else:
        if found != OUT_DIR:
            OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
            # Don’t move huge folder; just print resolved path to use in notebook
        print("CelebA folder detected at:", found.resolve())
        print("Use this path in your notebook for 'base_dir'.")

if __name__ == "__main__":
    main()