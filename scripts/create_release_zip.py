#!/usr/bin/env python3
"""
Creates a clean, production-ready zip archive of the PayScope project for upload/submission.
Excludes node_modules, .next, .git, and cache directories while preserving all
source files, documentation, public video assets, and working environment templates.
"""

import os
import subprocess
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = ROOT_DIR / "PayScope-release.zip"
PARENT_ZIP = ROOT_DIR.parent / "PayScope.zip"

def main():
    print(f"Creating clean git archive at: {OUTPUT_ZIP}")
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    # Step 1: Export repository HEAD via git archive
    subprocess.run(
        ["git", "archive", "--format=zip", "-o", str(OUTPUT_ZIP), "HEAD"],
        cwd=ROOT_DIR,
        check=True
    )

    # Step 2: Append working environment files if available so it runs immediately out-of-the-box
    env_files = [
        (ROOT_DIR / ".env", ".env"),
        (ROOT_DIR / "apps" / "api" / ".env", "apps/api/.env"),
        (ROOT_DIR / "apps" / "web" / ".env.local", "apps/web/.env.local"),
    ]

    with zipfile.ZipFile(OUTPUT_ZIP, mode="a", compression=zipfile.ZIP_DEFLATED) as zf:
        existing_names = set(zf.namelist())
        for file_path, arcname in env_files:
            if file_path.exists() and arcname not in existing_names:
                print(f"Adding configured environment: {arcname}")
                zf.write(file_path, arcname=arcname)

    # Step 3: Copy to parent directory as PayScope.zip for convenience
    try:
        import shutil
        shutil.copy2(OUTPUT_ZIP, PARENT_ZIP)
        print(f"Also created copy at: {PARENT_ZIP}")
    except Exception as e:
        print(f"Note: Could not copy to parent folder: {e}")

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    with zipfile.ZipFile(OUTPUT_ZIP, mode="r") as zf:
        total_files = len(zf.namelist())

    print(f"\nSuccessfully generated PayScope archive!")
    print(f"Archive Path : {OUTPUT_ZIP}")
    print(f"Archive Size : {size_mb:.2f} MB")
    print(f"Total Files  : {total_files} files packaged")

if __name__ == "__main__":
    main()
