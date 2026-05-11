"""Provides functions to query and update recently used files."""

from __future__ import annotations

import os

_STORAGE_PATH = os.path.join(os.path.expanduser("~"), ".local", "share", "missionDMX")
_STORAGE_FILE = os.path.join(_STORAGE_PATH, "recently_used.list")

if not os.path.exists(_STORAGE_PATH):
    os.makedirs(_STORAGE_PATH, mode=0o770, exist_ok=True)

if not os.path.exists(_STORAGE_FILE):
    with open(_STORAGE_FILE, "w") as f:
        f.write("")
    del f

def get_recently_used_files() -> list[str]:
    """This method returns the list of recently used files.

    Returns:
        A list of the recently used files in descending order.
    """
    real_entries = []
    with open(_STORAGE_FILE, "r") as f:
        entries = f.readlines()
        for entry in entries:
            if entry.strip() == "":
                continue
            real_entries.append(entry.replace("\n", ""))
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
