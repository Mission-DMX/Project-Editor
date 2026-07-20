"""Provides functions to query and update recently used files."""

from __future__ import annotations

from pathlib import Path

_STORAGE_PATH = Path.home() / ".local" / "share" / "missionDMX"
_STORAGE_FILE = _STORAGE_PATH / "recently_used.list"

_STORAGE_PATH.mkdir(parents=True, mode=0o770, exist_ok=True)

if not _STORAGE_FILE.exists():
    _STORAGE_FILE.touch()


def get_recently_used_files() -> list[str]:
    """Method returns the list of recently used files.

    Returns:
        A list of the recently used files in descending order.

    """
    return [
        entry
        for entry in _STORAGE_FILE.read_text(encoding="utf-8").splitlines()
        if entry.strip() and Path(entry).exists()
    ]


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

    _STORAGE_FILE.write_text(
        "\n".join(entries[:10]),
        encoding="utf-8",
    )
