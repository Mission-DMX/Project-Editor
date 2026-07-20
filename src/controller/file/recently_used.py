"""Provides functions to query and update recently used files."""

from __future__ import annotations

import os
from pathlib import Path

_STORAGE_PATH = os.path.join(os.path.expanduser("~"), ".local", "share", "missionDMX")
_STORAGE_FILE = os.path.join(_STORAGE_PATH, "recently_used.list")

if not Path(_STORAGE_PATH).exists():
    os.makedirs(_STORAGE_PATH, mode=0o770, exist_ok=True)

if not Path(_STORAGE_FILE).exists():
    with open(_STORAGE_FILE, "w") as f:
        f.write("")
    del f

def get_recently_used_files() -> list[str]:
    """Method returns the list of recently used files.

    Returns:
        A list of the recently used files in descending order.

    """
    real_entries = []
    with open(_STORAGE_FILE, "r") as f:
        entries = f.readlines()
        for entry in entries:
            clean_file_path = entry.replace("\n", "").strip()
            if clean_file_path == "":
                continue
            if Path(clean_file_path).exists():
                real_entries.append(clean_file_path)
    return real_entries

def register_opened_file(path: str) -> None:
    """Registers a file as being opened.

    Args:
        path: The path to the file which was opened.

    """
    path = os.path.expanduser(path.strip())
    existing_entries = get_recently_used_files()
    new_entries = [path]
    new_entries.extend(f"\n{entry}" for i, entry in enumerate(existing_entries) if
                       entry.strip() != "" and entry != path and i < 10)
    with open(_STORAGE_FILE, "w") as output_file:
        output_file.writelines(new_entries)
