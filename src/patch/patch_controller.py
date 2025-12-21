"""Controller for Patch mode."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from PySide6 import QtCore
from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsScene, QStackedWidget

from model import Universe
from patch.patch_plan.auto_resize_view import AutoResizeView
from patch.patch_plan.dialogs.universe_dialog import UniverseDialog
from patch.patch_plan.patch_item.background_view import BackgroundView
from patch.patch_plan.patch_item.clickable_view import ClickableView
from patch.patch_plan.patch_item.log_dmx.log_dmx_model import LogDmxModel
from patch.patch_plan.patch_item.log_dmx.log_dmx_view import LogDMXView
from patch.patch_plan.patch_item.used_fixture_view import UsedFixtureView
from patch.patch_plan.patch_plan_selector_view import PatchPlanSelectorView
from view.dialogs.fixture_dialog import FixtureDialog
from view.patch_view.patching.patching_select_view import PatchingSelectView

if TYPE_CHECKING:
    import proto.DirectMode_pb2
    from model import BoardConfiguration
    from model.ofl.fixture import UsedFixture
    from view.main_window import MainWindow


class PatchController(QObject):
    """Controller for Patch mode."""

    def __init__(self, board_configuration: BoardConfiguration, parent_view: MainWindow) -> None:
        """Patch Mode Controller."""
        super().__init__()
        self._board_configuration = board_configuration
        self._broadcaster = self._board_configuration.broadcaster
        self._dialog = None
        self._log_interval: int = 1

        self._patch_planes: dict[Universe, tuple[AutoResizeView, LogDmxModel]] = {}
        self._fixture_items: dict[UsedFixture, UsedFixtureView] = {}

        self._patch_view: QStackedWidget = QStackedWidget(parent_view)

        self._patch_plan_selector_view: PatchPlanSelectorView = PatchPlanSelectorView(self._patch_view)
        self._patching_select_view: PatchingSelectView = PatchingSelectView(self._board_configuration, self._patch_view)
        self._patch_view.addWidget(self._patch_plan_selector_view)
        self._patch_view.addWidget(self._patching_select_view)

        self._patch_plan_selector_view.generate_universe.connect(self._generate_universe)
        self._patch_plan_selector_view.rename_universe.connect(self._rename_universe)
        self._patch_plan_selector_view.delete_universe_index.connect(self._delete_universe_index)
        self._patch_plan_selector_view.dmx_log.connect(self._dmx_log)
        self._patch_plan_selector_view.dmx_log_interval.connect(lambda x: self._timer.setInterval(x * 1000))

        self._broadcaster.add_universe.connect(self._add_universe)
        self._broadcaster.delete_universe.connect(self._delete_universe)
        self._broadcaster.add_fixture.connect(self._add_fixture)

        self._broadcaster.view_to_patch_menu.connect(lambda: self.view.setCurrentIndex(0))
        self._broadcaster.view_patching.connect(lambda: self.view.setCurrentIndex(1))
        self._broadcaster.view_leave_patching.connect(lambda: self.view.setCurrentIndex(0))
        self._broadcaster.dmx_from_fish.connect(self._dmx_from_fish)

        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._request_dmx_data)

    @property
    def view(self) -> QStackedWidget:
        """Patch View."""
        return self._patch_view

    def _generate_universe(self) -> None:
        """Generate a new Universe by Dialog."""
        self._dialog = UniverseDialog(self._board_configuration.next_universe_id())
        if self._dialog.exec():
            Universe(self._dialog.output)

    def _add_universe(self, universe: Universe) -> None:
        """Handle, add a new universe."""
        index = self._patch_plan_selector_view.tabBar().count() - 1
        scene = QGraphicsScene(self)
        view = AutoResizeView(scene)
        view.setRenderHints(view.renderHints() | QPainter.RenderHint.Antialiasing)
        view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        background = BackgroundView()
        scene.addItem(background)
        log_dmx_model = LogDmxModel()
        dmx_data_log = LogDMXView(log_dmx_model)
        scene.addItem(dmx_data_log)
        clickable = ClickableView()
        clickable.channel_value_change.connect(partial(self._update_value, universe))
        scene.addItem(clickable)
        self._patch_planes.update({universe: (view, log_dmx_model)})
        self._patch_plan_selector_view.insertTab(index, view, str(universe.name))

    def _delete_universe_index(self, index: int) -> None:
        universe: Universe = list(self._patch_planes.keys())[index]
        self._broadcaster.delete_universe.emit(universe)

    def _delete_universe(self, universe: Universe) -> None:
        """Handle remove a universe."""
        widget = self._patch_planes[universe][0]
        self._patch_plan_selector_view.removeTab(self._patch_plan_selector_view.indexOf(widget))
        del self._patch_planes[universe]

    def _rename_universe(self, index: int) -> None:
        universe: Universe = list(self._patch_planes.keys())[index]
        dialog = UniverseDialog(universe.universe_proto)
        if dialog.exec():
            universe.universe_proto = dialog.output
            self._broadcaster.send_universe.emit(self._board_configuration.universe(index))

    def _add_fixture(self, fixture: UsedFixture) -> None:
        new_widget = UsedFixtureView(fixture)
        new_widget.modify_fixture.connect(self._modify_fixture)
        fixture.universe_changed.connect(partial(self._switch_universe, fixture))
        self._fixture_items[fixture] = new_widget
        self._patch_planes[fixture.universe][0].scene().addItem(new_widget)

    def _switch_universe(self, fixture: UsedFixture, old_universe: Universe) -> None:
        widget = self._fixture_items[fixture]
        self._patch_planes[old_universe][0].scene().removeItem(widget)
        self._patch_planes[fixture.universe][0].scene().addItem(widget)

    def _modify_fixture(self, fixture: UsedFixture) -> None:
        """Modify clicked Fixture."""
        self._dialog = FixtureDialog(fixture, self._board_configuration)
        self._dialog.show()

    def _request_dmx_data(self) -> None:
        """Send Signal to request dmx data from fish for each universe."""
        for universe in self._board_configuration.universes:
            self._broadcaster.send_request_dmx_data.emit(universe)

    def _dmx_log(self, run: bool) -> None:
        if run:
            self._timer.start()
        else:
            self._timer.stop()

    def _dmx_from_fish(self, dmx: proto.DirectMode_pb2.dmx_output) -> None:
        """Handle dmx data signal from fish."""
        self._patch_planes[self._board_configuration.universe(dmx.universe_id)][1].current_values = list(
            dmx.channel_data[1:])  # TODO fish of by one

    def _update_value(self, universe: Universe, channel: int, value: int) -> None:
        """Update the value of a channel."""
        universe.channels[channel].value = value
