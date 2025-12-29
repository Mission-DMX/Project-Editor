"""Provides the universe browser widget."""
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

import proto.UniverseControl_pb2
from model import BoardConfiguration, Broadcaster, Universe
from model.ofl.fixture import UsedFixture
from model.ofl.fixture_channel import FixtureChannel
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem


def _location_to_string(
        location: int | proto.UniverseControl_pb2.Universe.ArtNet | proto.UniverseControl_pb2.Universe.USBConfig, ) -> str:
    if isinstance(location, proto.UniverseControl_pb2.Universe.ArtNet):
        return f"{location.ip_address}:{location.port}/{location.universe_on_device}"
    if isinstance(location, proto.UniverseControl_pb2.Universe.USBConfig):
        return f"USB:{location.serial}"
    if isinstance(location, int):
        return f"local/{location}"

    return str(location)


def _generate_channel(index: int, channel: FixtureChannel) -> QTreeWidgetItem:
    return QTreeWidgetItem([str(index), str(channel.name)])  # TODO noch mehr anzeigen?


class UniverseTreeBrowserWidget(QTreeWidget):
    """Displays a browser for the fixtures within the universes."""

    def __init__(self, show: BoardConfiguration | None = None, show_selection_checkboxes: bool = False,
                 parent: QWidget = None) -> None:
        """Create a new universe browser instance.

        Args:
            show: The current active show file.
            show_selection_checkboxes: If true, checkboxes to select individual items are provided.
                Disabled by default.

        """
        super().__init__(parent)
        self._universes: dict[Universe, QTreeWidgetItem] = {}
        self._broadcaster = Broadcaster()
        self._show_selection_checkboxes = show_selection_checkboxes
        self.setColumnCount(4 if not show_selection_checkboxes else 5)
        self._show: BoardConfiguration | None = show
        self._currently_show_file_loading = False
        # TODO in Controller
        self._broadcaster.add_universe.connect(self.add_universe)
        self._broadcaster.add_fixture.connect(self.add_fixture)
        self._broadcaster.delete_universe.connect(self.delete_universe)

    def add_universe(self, universe: Universe) -> None:
        """Add a universe to the browser."""
        new_item = QTreeWidgetItem(
            [str(universe.id), str(universe.name), _location_to_string(universe.location), str(universe.description)])
        self._universes.update({universe: new_item})
        self.addTopLevelItem(new_item)

    def delete_universe(self, universe: Universe) -> None:
        """Delete a universe from the browser."""
        self.takeTopLevelItem(self.indexOfTopLevelItem(self._universes[universe]))
        del self._universes[universe]

    def add_fixture(self, fixture: UsedFixture) -> None:
        """Add a fixture to the browser."""
        if fixture.universe not in self._universes:
            return
        new_item = AnnotatedTreeWidgetItem(self._universes[fixture.universe],
                                           [f"{fixture.start_index + 1}", fixture.name_on_stage, str(fixture.mode),
                                            fixture.comment], fixture)
        fixture.universe_changed.connect(partial(self._fixture_change_universe, fixture, new_item))
        fixture.static_data_changed.connect(partial(self._fixture_change_data, new_item))
        fixture.delete_fixture.connect(partial(self.delete_fixture, new_item))

        for index, channel in enumerate(fixture.fixture_channels):
            new_item.addChild(_generate_channel(fixture.start_index + 1 + index, channel))
        self._universes[fixture.universe].sortChildren(0, Qt.SortOrder.AscendingOrder)

    def delete_fixture(self, item: AnnotatedTreeWidgetItem) -> None:
        """Delete a fixture from the browser."""
        item.parent().removeChild(item)

    def _fixture_change_universe(self, fixture: UsedFixture, item: AnnotatedTreeWidgetItem,
                                 old_universe: Universe) -> None:
        self._universes[old_universe].removeChild(item)
        self._universes[fixture.universe].addChild(item)
        self._universes[fixture.universe].sortChildren(0, Qt.SortOrder.AscendingOrder)

    def _fixture_change_data(self, item: AnnotatedTreeWidgetItem) -> None:
        fixture: UsedFixture = item.annotated_data
        item.setText(0, f"{fixture.start_index + 1}")
        item.setText(1, fixture.name_on_stage)
        item.setText(2, str(fixture.mode))
        item.setText(3, fixture.comment)
        for index, child in enumerate(item.takeChildren()):
            child.setText(0, f"{fixture.start_index + 1 + index}")
            item.addChild(child)

    def get_selected_fixtures(self) -> list[UsedFixture]:
        """Get a list of all fixture instances the user has selected."""
        a = []
        if not self._show_selection_checkboxes:
            return a
        for tli_index in range(self.topLevelItemCount()):
            tli = self.topLevelItem(tli_index)
            for fixture_item_index in range(tli.childCount()):
                fixture_item = tli.child(fixture_item_index)
                if not isinstance(fixture_item, AnnotatedTreeWidgetItem):
                    raise TypeError("Expected Annotated Tree Widget Item.")
                if not isinstance(fixture_item.annotated_data, UsedFixture):
                    raise TypeError("Expected data of TreeWidgetItem to be a fixture.")
                if fixture_item.checkState(0) == Qt.CheckState.Checked:
                    a.append(fixture_item.annotated_data)
        return a
