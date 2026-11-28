"""Shared helpers to sanitize and validate filter channel/group names.

Filter channel names appear in filter IDs, network update messages and serialized show
files. The rules enforced here are the ones required by filters that build channel names
dynamically from user-provided identifiers (color director, dimmer director).
"""

from __future__ import annotations


def sanitize_channel_name(name: str) -> str:
    """Remove characters that are problematic within channel names from the provided name.

    Args:
        name: The channel name to sanitize.

    Returns:
        The sanitized channel name.

    """
    return name.strip().replace(":", "").replace("#", "").replace("|", "").replace(" ", "_").replace("__", "-")


def is_valid_channel_name(name: str) -> bool:
    """Check whether the provided group or sub output name may be used.

    Only ASCII letters, digits, single underscores and hyphens are allowed since the names
    are used within filter ids, network update messages and serialized show files.

    Args:
        name: The name to check.

    Returns:
        True if the name is valid and can be used as a channel name.

    """
    if len(name) == 0 or "__" in name or name.endswith("_") or not name.isascii():
        return False
    return all(char.isalnum() or char in "_-" for char in name)
