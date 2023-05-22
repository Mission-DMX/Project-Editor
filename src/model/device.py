# coding=utf-8
"""DMX device"""
class Device:
    """A DMX device"""

    def __init__(self, name: str):
        self._name: str = name

    @property
    def name(self) -> str:
        """ID of the dmx device"""
        return self._name
