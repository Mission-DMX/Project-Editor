# coding=utf-8
"""Channels for patching"""
from PySide6 import QtCore



class PatchingChannel(QtCore.QObject):
    """Channels for patching to reduce redundancy over scenes"""

    updated_fixture: QtCore.Signal = QtCore.Signal()
    updated_color: QtCore.Signal = QtCore.Signal(str)

    def __init__(self, channel_address: int):
        """Constructs a patching channel."""
        super().__init__()
        if 0 > channel_address or channel_address > 511:
            raise ValueError(f"Tried to create a channel with address {channel_address}")
        self._address: int = channel_address

    @property
    def address(self) -> int:
        """Address of the channel. 0-indexed"""
        return self._address

