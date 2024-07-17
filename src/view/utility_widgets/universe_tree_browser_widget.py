# coding=utf-8

"""This file provides the universe browser widget."""

from PySide6.QtCore.Qt import Qt
from PySide6.QtWidgets import QTreeWidget

from proto.UniverseControl_pb2 import Universe as pbUniverse

from model.ofl.fixture import UsedFixture
from model import BoardConfiguration
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem


class UniverseTreeBrowserWidget(QTreeWidget):
    """This widget displays a browser for the fixtures within the universes."""
    def __init__(self, show: BoardConfiguration | None = None, show_selection_checkboxes: bool = False):
        super().__init__()
        self._show_selection_checkboxes = show_selection_checkboxes
        self.setColumnCount(4 if not show_selection_checkboxes else 5)
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
                if self._show_selection_checkboxes:
                    column_offset = 1
                else:
                    column_offset = 0
                item.setText(0 + column_offset, str(universe.id))
                item.setText(1 + column_offset, str(universe.name))
                item.setText(2 + column_offset, location_to_string(universe.location))
                item.setText(3 + column_offset, str(universe.description))
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
                        if self._show_selection_checkboxes:
                            last_fixture_object.setCheckState(0, Qt.CheckState.Unchecked)
                        last_fixture_object.setText(0 + column_offset, "{}/{}".format(universe.id, patching_channel.address + 1))
                        last_fixture_object.setText(1 + column_offset, channel_fixture.name)
                        last_fixture_object.setText(2 + column_offset, str(channel_fixture.mode))
                        last_fixture_object.setText(3 + column_offset, channel_fixture.comment)
                        last_fixture_object.annotated_data = channel_fixture
                        placed_fixtures.add(channel_fixture)
                    if not is_placeholder:
                        channel_item = AnnotatedTreeWidgetItem(last_fixture_object)
                        channel_item.setText(0 + column_offset, "{}/{}".format(universe.id, patching_channel.address + 1))
                        channel_item.setText(1 + column_offset, str(patching_channel.fixture_channel))
                        channel_item.setText(2 + column_offset, str(channel_fixture.mode))
                        channel_item.setText(3 + column_offset, channel_fixture.name)
                        channel_item.annotated_data = patching_channel
                i += 1

    def get_selected_fixtures(self) -> list[UsedFixture]:
        a = []
        if not self._show_selection_checkboxes:
            return a
        for tli_index in range(self.topLevelItemCount()):
            tli = self.topLevelItem(tli_index)
            for fixture_item_index in range(tli.childCount()):
                fixture_item = tli.child(fixture_item_index)
                if not isinstance(fixture_item, AnnotatedTreeWidgetItem):
                    raise ValueError("Expected Annotated Tree Widget Item.")
                if not isinstance(fixture_item.annotated_data, UsedFixture):
                    raise ValueError("Expected data of TreeWidgetItem to be a fixture.")
                if fixture_item.checkState(0) == Qt.CheckState.Checked:
                    a.append(fixture_item.annotated_data)
        return a
