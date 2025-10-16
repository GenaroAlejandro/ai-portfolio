# Universal dataset fetcher for the GfG "21-Days-21-Projects-Dataset" repo
# Usage (from repo root):
#   conda activate titanic_eda
#   python fetch_gfg.py
#
# How it works:
# - Clones the public dataset repo into a temp folder under ai-portfolio/.data_tmp
# - Copies any files listed in TASKS into their assignment data/ folders
# - Cleans up the temp folder (Windows-safe)
#
# Add more datasets by appending to TASKS below.

from pathlib import Path
import subprocess
import shutil
import os, stat, time

# ---------- Configure what to copy ----------
# Left:  source path inside the GfG repo
# Right: destination path inside repo
TASKS = [
    ("Datasets/Titanic-Dataset.csv", "assignments/titanic_eda/data/titanic.csv"),
    # Examples for future assignments:
    # ("Datasets/Iris.csv", "assignments/iris_eda/data/iris.csv"),
    # ("Datasets/Spam_or_Not_Spam.csv", "assignments/spam_eda/data/spam.csv"),
]

REPO_URL = "https://github.com/GeeksforgeeksDS/21-Days-21-Projects-Dataset"

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parent                     # ai-portfolio/
TMP = ROOT / ".data_tmp"                                   # temp clone here (ignored)
# Ensure all destination folders exist
for _, dst in TASKS:
    (ROOT / dst).parent.mkdir(parents=True, exist_ok=True)

# ---------- Robust cleanup for Windows (handles read-only .git files) ----------
def remove_readonly(func, path, _):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except PermissionError:
        time.sleep(0.1)
        os.chmod(path, stat.S_IWRITE)
        func(path)

def rmtree_safe(path: Path):
    if path.exists():
        shutil.rmtree(path, onerror=remove_readonly)

# ---------- Main ----------
def main():
    # 0) Fresh temp
    rmtree_safe(TMP)

    # 1) Shallow clone
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(TMP)], check=True)

    # 2) Copy each requested dataset
    for src_rel, dst_rel in TASKS:
        src = TMP / src_rel
        dst = ROOT / dst_rel
        if not src.is_file():
            print(f"❌ Not found in repo: {src_rel}")
            continue
        shutil.copy2(src, dst)
        print(f"✅ Copied: {src_rel}  ->  {dst_rel}")

    # 3) Clean temp
    rmtree_safe(TMP)
    print("✨ Done. Temp cleaned.")

if __name__ == "__main__":
    main()
