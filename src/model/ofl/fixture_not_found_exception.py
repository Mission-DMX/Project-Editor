from __future__ import annotations

import os


class FixtureDefNotFoundError(Exception):
    """Exception raised when fixture definition could not be found on disk."""

    def __init__(self, fixture_path: str, further_info: str) -> None:
        """Initialize with default message and provided fixture info."""
        super().__init__("Fixture Definition Not Found")
        self.fixture_path = fixture_path
        self.further_info = further_info

    def __str__(self) -> str:
        """Generate reasonable error message for observing human."""
        return f"Failed to load fixture {self.fixture_path}.\n{"File not Found.\n" if not
        os.path.exists(self.fixture_path) else ""}Further info: {self.further_info}"
