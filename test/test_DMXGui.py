from unittest import TestCase

from model.channel import Channel
from src.style import Style
from view.console_mode.console_channel_widget import ChannelWidget


class TestChannelWidget(TestCase):
    def test_max_button(self):
        channel = Channel(0)
        channel_widget = ChannelWidget(channel)

        channel_widget._max_button.click()
        self.assertEquals(channel.value, 255)
        self.assertEquals(channel_widget._slider.value(), 255)
        self.assertEquals(channel_widget._max_button.styleSheet(), Style.ACTIVE_BUTTON)
        self.assertEquals(channel_widget._min_button.styleSheet(), Style.BUTTON)

    def test_min_button(self):
        channel = Channel(0)
        channel_widget = ChannelWidget(channel)

        channel_widget._min_button.click()
        self.assertEquals(channel.value, 0)
        self.assertEquals(channel_widget._slider.value(), 0)
        self.assertEquals(channel_widget._min_button.styleSheet(), Style.ACTIVE_BUTTON)
        self.assertEquals(channel_widget._max_button.styleSheet(), Style.BUTTON)

    def test_slider(self):
        channel = Channel(0)
        channel_widget = ChannelWidget(channel)

        channel_widget._slider.setValue(69)
        self.assertEquals(channel.value, 69)
        self.assertEquals(channel_widget._slider.value(), 69)
        self.assertEquals(channel_widget._max_button.styleSheet(), Style.BUTTON)
        self.assertEquals(channel_widget._min_button.styleSheet(), Style.BUTTON)

    def test_slider_max(self):
        channel = Channel(0)
        channel_widget = ChannelWidget(channel)

        channel_widget._slider.setValue(255)
        self.assertEquals(channel.value, 255)
        self.assertEquals(channel_widget._slider.value(), 255)
        self.assertEquals(channel_widget._max_button.styleSheet(), Style.ACTIVE_BUTTON)
        self.assertEquals(channel_widget._min_button.styleSheet(), Style.BUTTON)

    def test_slider_min(self):
        channel = Channel(0)
        channel_widget = ChannelWidget(channel)

        channel_widget._slider.setValue(96)
        channel_widget._slider.setValue(0)
        self.assertEquals(channel.value, 0)
        self.assertEquals(channel_widget._slider.value(), 0)
        self.assertEquals(channel_widget._max_button.styleSheet(), Style.BUTTON)
        self.assertEquals(channel_widget._min_button.styleSheet(), Style.ACTIVE_BUTTON)
