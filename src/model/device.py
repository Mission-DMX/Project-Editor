"""DMX device"""


class Device:
    """A DMX device"""

    def __init__(self, name: str) -> None:
        self._name: str = name

    @property
    def name(self) -> str:
        """ID of the dmx device"""
        return self._name
