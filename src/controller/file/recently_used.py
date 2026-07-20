"""Provides functions to query and update recently used files."""

from __future__ import annotations

from pathlib import Path

_STORAGE_PATH = Path.home() / ".local" / "share" / "missionDMX"
_STORAGE_FILE = _STORAGE_PATH / "recently_used.list"


def init_recently_used_storage() -> None:
    """Initialize the storage path and file for recently used files.

    This must be called once during application startup before any other
    functions in this module are used.
    """
    _STORAGE_PATH.mkdir(parents=True, mode=0o770, exist_ok=True)

    if not _STORAGE_FILE.exists():
        _STORAGE_FILE.touch()


def get_recently_used_files() -> list[str]:
    """Method returns the list of recently used files.

    Returns:
        A list of the recently used files in descending order.

    """
    real_entries = []
    for entry in _STORAGE_FILE.read_text().splitlines():
        clean_file_path = entry.strip()
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
    path = Path(path.strip()).expanduser().as_posix()
    existing_entries = get_recently_used_files()
    new_entries = [path]
    new_entries.extend(
        f"\n{entry}" for i, entry in enumerate(existing_entries) if entry.strip() != "" and entry != path and i < 10
    )
    _STORAGE_FILE.write_text("".join(new_entries))
