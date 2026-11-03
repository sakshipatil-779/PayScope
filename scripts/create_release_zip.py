#!/usr/bin/env python3
"""
Creates a clean, production-ready zip archive of the PayScope project with all current working changes.
Excludes node_modules, .next, .git, and cache directories while preserving all
source files, documentation, public video assets, and working environment files.
Does not push anything to GitHub.
"""

import os
import shutil
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = ROOT_DIR / "PayScope-release.zip"
PARENT_ZIP = ROOT_DIR.parent / "PayScope.zip"

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "ENV",
    "env",
    ".turbo",
    "playwright-report",
    "test-results",
}

EXCLUDE_EXTS = {
    ".zip",
    ".tar.gz",
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
}

def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    if path.suffix.lower() in EXCLUDE_EXTS:
        return True
    if path.name.startswith(".coverage"):
        return True
    return False

def main():
    print(f"Packaging PayScope workspace with all current changes into: {OUTPUT_ZIP}")
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    if PARENT_ZIP.exists():
        try:
            PARENT_ZIP.unlink()
        except Exception:
            pass

    file_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Prune excluded directories in-place so os.walk does not recurse into them
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file_name in files:
                file_path = Path(root) / file_name
                rel_path = file_path.relative_to(ROOT_DIR)
                
                if is_excluded(rel_path):
                    continue
                
                # Use forward slashes in archive
                arcname = rel_path.as_posix()
                zf.write(file_path, arcname=arcname)
                file_count += 1

    # Also copy to parent directory as PayScope.zip
    try:
        shutil.copy2(OUTPUT_ZIP, PARENT_ZIP)
        print(f"Also created copy at: {PARENT_ZIP}")
    except Exception as e:
        print(f"Note: Could not copy to parent folder: {e}")

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"\nSuccessfully created updated PayScope archive with all working changes!")
    print(f"Archive Path : {OUTPUT_ZIP}")
    print(f"Archive Size : {size_mb:.2f} MB")
    print(f"Total Files  : {file_count} files packaged")

if __name__ == "__main__":
    main()
