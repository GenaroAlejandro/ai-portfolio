# Simple fetch script (Windows-safe cleanup)
import subprocess
from pathlib import Path
import shutil, os, stat, time

data_dir = Path(__file__).resolve().parents[1] / "data"
data_dir.mkdir(parents=True, exist_ok=True)

tmp = data_dir / "_gfg_tmp"
# Clean temp if it exists (handle read-only files on Windows)
def handle_remove_readonly(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)  # remove read-only attribute
        func(path)
    except PermissionError:
        time.sleep(0.1)                # tiny wait, then retry once
        os.chmod(path, stat.S_IWRITE)
        func(path)

if tmp.exists():
    shutil.rmtree(tmp, onerror=handle_remove_readonly)

# 1) Shallow clone to temp
subprocess.run([
    "git", "clone", "--depth", "1",
    "https://github.com/GeeksforgeeksDS/21-Days-21-Projects-Dataset",
    str(tmp)
], check=True)

# 2) Copy Titanic CSV
shutil.copy2(tmp / "Datasets" / "Titanic-Dataset.csv", data_dir / "titanic.csv")

# 3) Clean temp (Windows-safe)
shutil.rmtree(tmp, onerror=handle_remove_readonly)

print(f"✅ Titanic dataset saved to {data_dir/'titanic.csv'}")