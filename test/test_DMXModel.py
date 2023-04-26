from unittest import TestCase
from src.DMXModel import Channel, Universe


class TestChannel(TestCase):
    def test_valid_address(self):
        address = 10
        channel = Channel(address)
        self.assertEqual(address, channel.address)

    def test_invalid_address(self):
        invalid_address = -1
        self.assertRaises(ValueError, Channel, invalid_address)
        invalid_address = 588
        self.assertRaises(ValueError, Channel, invalid_address)

    def test_valid_value(self):
        channel = Channel(0)
        self.assertEqual(0, channel.value)

    def test_valid_update(self):
        channel = Channel(0)
        new_value = 167

        channel.updated.connect(lambda x: self.assertEqual(new_value, x))
        channel.updated.connect(lambda x: self.assertEqual(new_value, channel.value))
        channel.value = new_value

    def test_invalid_update(self):
        channel = Channel(0)
        value = -1
        with self.assertRaises(ValueError):
            channel.value = value
        value = 288
        with self.assertRaises(ValueError):
            channel.value = value


class TestUniverse(TestCase):
    def test_valid_address(self):
        address = 12
        universe = Universe(address)
        self.assertEqual(address, universe.universe_proto.id)

    def test_invalid_address(self):
        address = -5
        self.assertRaises(ValueError, Universe, address)

    def test_channels(self):
        universe = Universe(0)
        self.assertEqual(512, len(universe.channels))
        last_address = -1
        for channel in universe.channels:
            self.assertEqual(0, channel.value)
            self.assertEqual(last_address + 1, channel.address)
            last_address += 1
