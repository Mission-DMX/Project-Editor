# coding=utf-8

"""This file provides the universe browser widget."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget

import proto.UniverseControl_pb2
from model import BoardConfiguration, Broadcaster
from model.ofl.fixture import UsedFixture
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem


class UniverseTreeBrowserWidget(QTreeWidget):
    """This widget displays a browser for the fixtures within the universes."""

    def __init__(self, show: BoardConfiguration | None = None, show_selection_checkboxes: bool = False):
        super().__init__()
        self._broadcaster = Broadcaster()
        self._show_selection_checkboxes = show_selection_checkboxes
        self.setColumnCount(4 if not show_selection_checkboxes else 5)
        self._show: BoardConfiguration | None = show
        if self._show:
            self.refresh()
            self._broadcaster.add_universe.connect(self.refresh)
            self._broadcaster.delete_universe.connect(self.refresh)
            self._broadcaster.add_fixture.connect(lambda _: self.refresh())

    def refresh(self):

        def location_to_string(location):
            if isinstance(location, proto.UniverseControl_pb2.Universe.ArtNet):
                return f"{location.ip_address}:{location.port}/{location.universe_on_device}"
            if isinstance(location, proto.UniverseControl_pb2.Universe.USBConfig):
                return f"USB:{location.serial}"
            if isinstance(location, int):
                return f"local/{location}"

            return str(location)

        self.clear()
        i = 0
        if self._show:
            for universe in self._show.universes.values():
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
                for fixture in self._broadcaster.fixtures:
                    last_fixture_object = AnnotatedTreeWidgetItem(item)
                    if self._show_selection_checkboxes:
                        last_fixture_object.setCheckState(0, Qt.CheckState.Unchecked)
                    last_fixture_object.setText(0 + column_offset,
                                                f"{universe.id}/{fixture.start_index + 1}")
                    last_fixture_object.setText(1 + column_offset, fixture.name)
                    last_fixture_object.setText(2 + column_offset, str(fixture.mode))
                    last_fixture_object.setText(3 + column_offset, fixture.comment)
                    last_fixture_object.annotated_data = fixture
                    placed_fixtures.add(fixture)

                    for channel in fixture.fixture_channels:
                        channel_item = AnnotatedTreeWidgetItem(last_fixture_object)
                        channel_item.setText(0 + column_offset,
                                             f"{universe.id}/{fixture.start_index + 1}")
                        channel_item.setText(1 + column_offset, str(channel.name))
                        channel_item.setText(2 + column_offset, str(fixture.mode))
                        channel_item.setText(3 + column_offset, fixture.name)
                        # TODO channel_item.annotated_data = patching_channel

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
