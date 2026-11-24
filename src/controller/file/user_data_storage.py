"""Read and write simple line based user state into the local missionDMX data directory."""

import os
import tempfile
from contextlib import suppress
from pathlib import Path

_USER_STORAGE_PATH = Path.home() / ".local" / "share" / "missionDMX"
_USER_STORAGE_DIRECTORY_MODE = 0o770
_USER_STORAGE_FILE_MODE = 0o660


def _storage_file(file_name: str) -> Path:
    """Get the path of the given user storage file.

    Args:
        file_name: the name of the user storage file

    Returns:
        the path of the user storage file within the local missionDMX data directory

    Raises:
        ValueError: if the given file name is not a plain file name, for example if it contains a
            path separator or refers to the current or a parent directory

    """
    if not file_name or file_name in {".", ".."} or Path(file_name).name != file_name:
        raise ValueError(f"{file_name!r} is not a valid user storage file name.")
    return _USER_STORAGE_PATH / file_name


def _ensure_storage_directory() -> None:
    """Create the user storage directory if it does not exist yet."""
    _USER_STORAGE_PATH.mkdir(parents=True, mode=_USER_STORAGE_DIRECTORY_MODE, exist_ok=True)
    with suppress(OSError):
        _USER_STORAGE_PATH.chmod(_USER_STORAGE_DIRECTORY_MODE)


def read_stored_lines(file_name: str) -> list[str]:
    """Read the non empty lines of the given user storage file.

    Args:
        file_name: the name of the user storage file to read

    Returns:
        the stripped, non empty lines of the storage file or an empty list if the file does not exist

    Raises:
        ValueError: if the given file name is not a valid user storage file name
        OSError: if the storage file exists but cannot be read

    """
    try:
        content = _storage_file(file_name).read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    entries: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            entries.append(stripped)
    return entries


def write_stored_lines(file_name: str, lines: list[str]) -> None:
    """Write the given lines into the user storage file, replacing its previous content.

    Blank lines are dropped. The user storage directory is created if it does not exist yet.

    Args:
        file_name: the name of the user storage file to write
        lines: the lines to store

    Raises:
        ValueError: if the given file name is not a valid user storage file name
        OSError: if the user storage file cannot be written

    """
    storage_file = _storage_file(file_name)
    _ensure_storage_directory()
    temp_fd, temp_name = tempfile.mkstemp(dir=_USER_STORAGE_PATH, prefix=file_name + ".", suffix=".tmp")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as temp_file:
            temp_file.write("".join(line + "\n" for line in lines if line))
            temp_file.flush()
            os.fsync(temp_file.fileno())
        with suppress(OSError):
            os.chmod(temp_name, _USER_STORAGE_FILE_MODE)
        os.replace(temp_name, storage_file)
    except BaseException:
        with suppress(OSError):
            os.unlink(temp_name)
        raise


def append_stored_line(file_name: str, line: str) -> None:
    """Append a single line to the user storage file.

    Args:
        file_name: the name of the user storage file to append to
        line: the line to append

    Raises:
        ValueError: if the given file name is not a valid user storage file name
        OSError: if the line cannot be appended

    """
    if not line:
        return
    storage_file = _storage_file(file_name)
    _ensure_storage_directory()
    with storage_file.open("a", encoding="utf-8") as file:
        file.write(line + "\n")
        file.flush()
        os.fsync(file.fileno())
    with suppress(OSError):
        storage_file.chmod(_USER_STORAGE_FILE_MODE)
