# coding=utf-8

"""This file provides the universe browser widget."""

from PySide6.QtWidgets import QTreeWidget

from proto.UniverseControl_pb2 import Universe as pbUniverse

from model.ofl.fixture import UsedFixture
from model import BoardConfiguration
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem


class UniverseTreeBrowserWidget(QTreeWidget):
    """This widget displays a browser for the fixtures within the universes."""
    def __init__(self, show: BoardConfiguration | None = None):
        super().__init__()
        self.setColumnCount(4)
        self._show: BoardConfiguration | None = show
        if self._show:
            self.refresh()
            self._show.broadcaster.add_universe.connect(self.refresh)
            self._show.broadcaster.delete_universe.connect(self.refresh)
            self._show.broadcaster.fixture_patched.connect(self.refresh)

    def refresh(self):

        def location_to_string(location):
            if isinstance(location, pbUniverse.ArtNet):
                return "{}:{}/{}".format(location.ip_address, location.port, location.universe_on_device)
            elif isinstance(location, pbUniverse.USBConfig):
                return "USB:{}".format(location.serial)
            elif isinstance(location, int):
                return "local/{}".format(location)
            else:
                return str(location)

        self.clear()
        i = 0
        if self._show:
            for universe in self._show.universes:
                item = AnnotatedTreeWidgetItem(self)
                item.setText(0, str(universe.id))
                item.setText(1, str(universe.name))
                item.setText(2, location_to_string(universe.location))
                item.setText(3, str(universe.description))
                item.setExpanded(True)
                item.annotated_data = universe
                self.insertTopLevelItem(i, item)
                placed_fixtures = set()
                last_fixture_object: AnnotatedTreeWidgetItem | None = None
                last_fixture: UsedFixture | None = None
                for patching_channel in universe.patching:
                    channel_fixture = patching_channel.fixture
                    is_placeholder = (channel_fixture == last_fixture) or channel_fixture.parent_universe == -1
                    last_fixture = channel_fixture
                    if not is_placeholder and (channel_fixture not in placed_fixtures or last_fixture_object is None):
                        last_fixture_object = AnnotatedTreeWidgetItem(item)
                        last_fixture_object.setText(0, "{}/{}".format(universe.id, patching_channel.address + 1))
                        last_fixture_object.setText(1, channel_fixture.name)
                        last_fixture_object.setText(2, str(channel_fixture.mode))
                        last_fixture_object.setText(3, channel_fixture.comment)
                        last_fixture_object.annotated_data = channel_fixture
                        placed_fixtures.add(channel_fixture)
                    if not is_placeholder:
                        channel_item = AnnotatedTreeWidgetItem(last_fixture_object)
                        channel_item.setText(0, "{}/{}".format(universe.id, patching_channel.address + 1))
                        channel_item.setText(1, str(patching_channel.fixture_channel))
                        channel_item.setText(2, str(channel_fixture.mode))
                        channel_item.setText(3, channel_fixture.name)
                        channel_item.annotated_data = patching_channel
                i += 1
