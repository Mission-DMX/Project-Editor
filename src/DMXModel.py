"""Provides data structures with accessors and modifiers for DMX"""

from PySide6 import QtCore


class Channel(QtCore.QObject):
    """Basic dmx channel with 256 values"""

    updated: QtCore.Signal = QtCore.Signal(int)

    def __init__(self, channel_address: int):
        """Constructs a channel."""
        super().__init__()
        assert 0 <= channel_address <= 511,\
            f"Tried to create a channel with address {channel_address}"
        self._address: int = channel_address
        self._value: int = 0

    @property
    def address(self) -> int:
        """Address of the channel. 0-indexed"""
        return self._address

    @property
    def value(self) -> int:
        """The current value of the channel"""
        return self._value

    def update(self, value: int) -> None:
        """Updates the value of the channel.
                Must be between 0 and 255.

                Raises:
                    AssertionError: The value is below 0 or above 255.
                """
        assert 0 <= value <= 255, f"Tried to set channel {self._address} to {value}."
        if value != self._value:
            self._value = value
            self.updated.emit(value)


class Device:
    """A DMX device"""

    def __init__(self, device_id: int, channels: list[Channel]):
        self._id: int = device_id
        self._channels: list[Channel] = channels

    @property
    def id(self) -> int:
        """ID of the dmx device"""
        return self._id

    @property
    def channels(self) -> list[Channel]:
        """List of DMX channels used by this device"""
        return self._channels


class Universe:
    """DMX universe with 512 channels"""

    def __init__(self, universe_id: int):
        self._id: int = universe_id
        self._channels: list[Channel] = [Channel(channel_address) for channel_address in range(512)]
        self._devices: list[Device] = []

    @property
    def id(self) -> int:
        """ID of the dmx universe. 0-indexed"""
        return self._id

    @property
    def channels(self) -> list[Channel]:
        """List of all 512 dmx channels belonging to the channel"""
        return self._channels

    @property
    def devices(self) -> list[Device]:
        """List of all registered DMX devices in this universe"""
        return self._devices

    def register_device(self, device: Device) -> None:
        """Registers an DMX device to this universe"""
        for existing_device in self._devices:
            exdev_start = existing_device.channels[0].address
            exdev_end = existing_device.channels[-1].address
            newdev_start = existing_device.channels[0].address
            newdev_end = existing_device.channels[-1].address

            # Address space of old/new device starts in address space of new/old device
            assert newdev_start > exdev_start > newdev_end and exdev_start > newdev_start > exdev_end, \
                f"Address conflict: Tried to register device {device.id} to {self._id}" \
                f"but address space overlaps with device {existing_device.id}"

            # Device id is unique
            assert existing_device.id is not device.id,\
                f"ID conflict: Tried to register device {device.id} to {self._id}"

        self._devices.append(device)

    def unregister_device(self, device: Device) -> None:
        """Removes a DMX device from this universe"""
        self._devices.remove(device)


class Scene:
    """Scene
    TODO implement
    """

    def __init__(self):
        pass


class Filter:
    """Filter
    TODO implement
    """

    def __init__(self):
        pass


class ConnectionTest:
    def __init__(self, universe: Universe):
        for channel in universe.channels:
            channel.updated.connect(lambda x, address=channel.address: print(f"Updated universe {universe.id} channel {address} to value {x}"))
