# coding=utf-8
"""Channels for patching"""
from PySide6 import QtCore

from ofl.fixture import Mode, UsedFixture


class PatchingChannel(QtCore.QObject):
    """Channels for patching to reduce redundancy over scenes"""

    updated_fixture: QtCore.Signal = QtCore.Signal()
    updated_color: QtCore.Signal = QtCore.Signal(str)

    def __init__(self, channel_address: int, color: str):
        """Constructs a patching channel."""
        super().__init__()
        if 0 > channel_address or channel_address > 511:
            raise ValueError(f"Tried to create a channel with address {channel_address}")
        self._address: int = channel_address
        parent_universe_id = -1
        self._fixture: UsedFixture = UsedFixture("Empty", "", set(), "", Mode(channels=["none"], shortName="", name=""),
                                                 "", 0, parent_universe_id)
        self._fixture_channel: int = 0
        self._color: str = color
        self._ignore_black = True

    @property
    def address(self) -> int:
        """Address of the channel. 0-indexed"""
        return self._address

    @property
    def fixture(self) -> UsedFixture:
        """The fixture of the channel"""
        return self._fixture

    @fixture.setter
    def fixture(self, fixture: UsedFixture):
        if self._fixture:
            try:
                self._fixture.channels.remove(self)
            except ValueError:
                pass
        self._fixture = fixture
        if self._fixture:
            self._fixture.channels.append(self)
        self.updated_fixture.emit()

    @property
    def ignore_black(self) -> bool:
        """The fixture of the channel"""
        return self._ignore_black

    @ignore_black.setter
    def ignore_black(self, ignore_black: bool):
        self._ignore_black = ignore_black

    @property
    def fixture_channel(self) -> str:
        """The use of this channel in Fixture"""
        return self._fixture.mode['channels'][self._fixture_channel]

    @fixture_channel.setter
    def fixture_channel(self, fixture_channel: int):
        self._fixture_channel = fixture_channel
        self.updated_fixture.emit()

    @property
    def color(self) -> str:
        """color of the fixture in PatchPlan"""
        return self._color

    @color.setter
    def color(self, color: str):
        self._color = color
        self.updated_color.emit(self._color)

    def fixture_channel_id(self) -> int:
        return self._fixture_channel
