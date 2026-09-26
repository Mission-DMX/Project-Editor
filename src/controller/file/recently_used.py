"""Provides functions to query and update recently used files."""

from __future__ import annotations

from pathlib import Path

from controller.file.user_data_storage import read_stored_lines, write_stored_lines

_STORAGE_FILE_NAME = "recently_used.list"
_MAX_RECENTLY_USED_ENTRIES = 10


def get_recently_used_files() -> list[str]:
    """Method returns the list of recently used files.

    Returns:
        A list of the recently used files in descending order.

    """
    return [entry for entry in read_stored_lines(_STORAGE_FILE_NAME) if Path(entry).exists()]


def register_opened_file(path: str) -> None:
    """Registers a file as being opened.

    Args:
        path: The path to the file which was opened.

    """
    path = str(Path(path.strip()).expanduser().resolve())

    entries = [
        path,
        *[entry for entry in get_recently_used_files() if entry != path],
    ]

    write_stored_lines(_STORAGE_FILE_NAME, entries[:_MAX_RECENTLY_USED_ENTRIES])
