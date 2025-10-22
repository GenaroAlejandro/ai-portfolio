#!/usr/bin/env python3
"""
fetch.py — Simple downloader for one dataset file.

Downloads ONE CSV (or similar) into this assignment's data/ folder.
You can use either:
  --path : path inside the GeeksforGeeks dataset repo
  --url  : any full RAW file URL (GitHub, Kaggle, etc.)
"""

import argparse, os
from urllib.request import urlretrieve          # simple function: downloads file to disk
from urllib.parse import urlparse               # helps extract the filename from URL

# ---------- CONSTANTS ----------
# Base RAW URL for the GeeksforGeeks dataset repository.
# If the repo ever moves, update this constant.
GFG_BASE = "https://raw.githubusercontent.com/GeeksforGeeksDS/21-Days-21-Projects-Dataset/main/"

# ---------- HELPER FUNCTION ----------
def raw_from_path(path: str) -> str:
    """Build a full URL from a repo path.
       Example: 'Datasets/netflix_titles.csv'
       becomes  'https://raw.githubusercontent.com/.../Datasets/netflix_titles.csv'
    """
    return f"{GFG_BASE.rstrip('/')}/{path.lstrip('/')}"

# ---------- MAIN SCRIPT ----------
def main():
    # Create the command-line interface (CLI)
    p = argparse.ArgumentParser(description="Fetch one dataset into ../data/")
    
    # Only one source allowed: either --path or --url
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--path", help="Repo path, e.g., Datasets/netflix_titles.csv")
    g.add_argument("--url",  help="Full RAW URL, e.g., https://.../file.csv")
    
    # Optional arguments
    p.add_argument("--name", help="Rename output file (defaults to the same name as in the URL/path)")
    p.add_argument("--force", action="store_true", help="Overwrite if the file already exists")
    
    args = p.parse_args()  # Parse all inputs from the terminal
    
    # --- 1) Decide final download URL ---
    url = args.url or raw_from_path(args.path)  # use --url as-is or build from --path

    # --- 2) Decide filename to save ---
    # If --name not given, take the last part of the path/URL (the file’s basename)
    basename_source = args.url or args.path
    filename = args.name or os.path.basename(urlparse(basename_source).path)

    # --- 3) Decide where to save inside THIS assignment ---
    # This script is in assignments/<assignment>/src/
    # So "../data" moves one level up to the "data" folder.
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    out_dir = os.path.abspath(out_dir)          # turn relative path into full path
    out_path = os.path.join(out_dir, filename)  # final full file path
    
    # --- 4) Skip if already downloaded (unless --force) ---
    if os.path.exists(out_path) and not args.force:
        print(f"[SKIP] {out_path} exists (use --force to overwrite)")
        return

    # --- 5) Ensure folder exists, then download ---
    os.makedirs(out_dir, exist_ok=True)         # create data/ if missing
    print(f"[GET ] {url}")
    print(f"[SAVE] {out_path}")
    
    # urlretrieve handles both download and saving to file
    urlretrieve(url, out_path)
    
    print("[DONE]")                             # friendly success message

# Run main() only if the script is executed directly (not imported as a module)
if __name__ == "__main__":
    main()
