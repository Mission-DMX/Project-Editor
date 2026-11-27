"""Shell editor widget for the property-based cue vfilter."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from model.virtual_filters.property_cues.model.model import EndAction
from model.virtual_filters.property_cues.model.property_cue import PropertyCue
from model.virtual_filters.property_cues.model.property_step import PropertyStep
from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter
from view.show_mode.editor.node_editor_widgets.cue_editor.preview_edit_widget import (
    ExternalChannelDefinition,
    PreviewEditWidget,
)
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.show_mode.editor.node_editor_widgets.property_cue_editor._board_lookups import (
    lookup_fixtures,
    resolve_node_name,
)
from view.show_mode.editor.node_editor_widgets.property_cue_editor._builders import build_root_ui
from view.show_mode.editor.node_editor_widgets.property_cue_editor._settings_panel import (
    refresh_default_cue_combo,
    refresh_settings_from_model,
)
from view.show_mode.editor.node_editor_widgets.property_cue_editor.preview_control import PreviewController

if TYPE_CHECKING:
    from model import Filter
    from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import PropertyPane
    from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import StepFixtureTree
    from view.show_mode.editor.nodes import FilterNode

logger = getLogger(__name__)


class PropertyCueEditor(PreviewEditWidget):
    """Property-based cue editor widget: cue table, step tree and property pane."""

    def __init__(self, f: Filter | None = None) -> None:
        """Initialize the shell editor widget."""
        super().__init__(f)
        self._property_filter: PropertyBasedCueFilter | None = f if isinstance(f, PropertyBasedCueFilter) else None
        if self._property_filter is None:
            logger.error("Property-cue editor received invalid filter: %s", f)
        self._root = QWidget()
        self._cue_table: QTableWidget | None = None
        self._end_action_combo: QComboBox | None = None
        self._restart_on_play_cb: QCheckBox | None = None
        self._persistence_cb: QCheckBox | None = None
        self._default_cue_combo: QComboBox | None = None
        self._configure_button: QPushButton | None = None
        self._preview_button: QPushButton | None = None
        self._add_cue_button: QPushButton | None = None
        self._add_step_button: QPushButton | None = None
        self._splitter: QSplitter | None = None
        self._step_tree_placeholder: QLabel | None = None
        self._property_pane_placeholder: QLabel | None = None
        self._step_tree: StepFixtureTree | None = None
        self._property_pane: PropertyPane | None = None
        self._wizard = None
        self._preview_prompt: YesNoDialog | None = None
        self._preview_controller: PreviewController | None = (
            PreviewController(self._property_filter) if self._property_filter is not None else None
        )
        self._preview_active = False
        build_root_ui(self)

    @property
    def step_tree_container(self) -> QWidget:
        """Return the placeholder widget that hosts the step/fixture tree."""
        return self._step_tree_placeholder

    @property
    def property_pane_container(self) -> QWidget:
        """Return the placeholder widget that hosts the property pane."""
        return self._property_pane_placeholder

    def _invalidate_cache(self) -> None:
        """Drop the vfilter's cached compile so the next preview rebuild uses current model state.

        L10: :meth:`PropertyBasedCueFilter.invalidate_compile_cache` is only
        called from this helper; every editor mutator that touches the
        property model routes through here. Without this the preview would
        render the pre-edit timeline until the dialog was closed and the
        next ``_rebuild_io`` dropped the cache.
        """
        if self._property_filter is not None:
            self._property_filter.invalidate_compile_cache()

    def _end_action_changed(self, text: str) -> None:
        cue = self._selected_cue()
        if cue is None:
            return
        try:
            cue.end_action = EndAction[text]
        except KeyError:
            logger.warning("Unknown end action: %s", text)
            return
        self._invalidate_cache()

    def _restart_on_play_toggled(self, checked: bool) -> None:
        cue = self._selected_cue()
        if cue is None:
            return
        cue.restart_on_play = checked
        self._invalidate_cache()

    def _selected_cue(self) -> PropertyCue | None:
        if self._property_filter is None or self._cue_table is None:
            return None
        idx = self._cue_table.currentRow()
        cues = self._property_filter.property_model.cues
        if 0 <= idx < len(cues):
            return cues[idx]
        return None

    def _cue_selection_changed(self) -> None:
        self._apply_cue_selection_state()
        # L11: anchor the preview playhead to whatever the user selects,
        # so pressing PLAY on the XTouch picks up at the right cue.
        if self._preview_active:
            self._preview_push_current_selection()

    def _on_step_tree_selection_changed(self, _step_index: int, _node_path: str) -> None:
        """L11: when the user picks a step in the tree, jump the preview to that step's start."""
        if self._preview_active:
            self._preview_push_current_selection()

    def _apply_cue_selection_state(self) -> None:
        cue = self._selected_cue()
        has_cue = cue is not None
        if self._end_action_combo is not None:
            self._end_action_combo.setEnabled(has_cue)
        if self._restart_on_play_cb is not None:
            self._restart_on_play_cb.setEnabled(has_cue)
        if self._add_step_button is not None:
            self._add_step_button.setEnabled(has_cue)
        self._refresh_settings_from_model()
        idx = -1
        if has_cue and self._cue_table is not None:
            idx = self._cue_table.currentRow()
        if self._step_tree is not None:
            self._step_tree.set_current_cue(idx)
        if self._property_pane is not None:
            self._property_pane.set_current_cue(idx)
        self._update_cue_step_button_state()

    def _add_cue(self) -> None:
        if self._property_filter is None or self._cue_table is None:
            return
        model = self._property_filter.property_model
        name = f"Cue {len(model.cues) + 1}"
        new_cue = PropertyCue(name=name, steps=[PropertyStep(name="Step 1")])
        model.cues.append(new_cue)
        self._invalidate_cache()
        self._refresh_cue_table()
        self._refresh_default_cue_combo()
        self._cue_table.selectRow(len(model.cues) - 1)

    def _add_step(self) -> None:
        cue = self._selected_cue()
        if cue is None:
            return
        cue.steps.append(PropertyStep(name=f"Step {len(cue.steps) + 1}"))
        self._invalidate_cache()
        self._refresh_cue_table()
        if self._step_tree is not None:
            self._step_tree.refresh()

    def _persistence_toggled(self, checked: bool) -> None:
        if self._property_filter is None:
            return
        self._property_filter.property_model.general.persistence = checked
        self._invalidate_cache()

    def _default_cue_changed(self, index: int) -> None:
        if self._property_filter is None:
            return
        self._property_filter.property_model.general.default_cue_index = index - 1
        self._invalidate_cache()

    def _board(self):  # noqa: ANN202 — BoardConfiguration imported lazily
        if self._property_filter is None:
            return None
        scene = self._property_filter.scene
        return getattr(scene, "board_configuration", None) if scene is not None else None

    def _launch_wizard(self) -> None:
        if self._property_filter is None:
            logger.error("No filter available; cannot launch wizard.")
            return
        board = self._board()
        if board is None:
            logger.error("No board configuration available; cannot launch wizard.")
            return
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard import (
            FixtureSelectionWizard,
        )
        self._wizard = FixtureSelectionWizard(
            board,
            initial=self._property_filter.property_model.fixture_selection,
            parent=self._root,
        )
        if self._wizard.exec():
            new_selection = self._wizard.result_selection()
            if new_selection is not None:
                self._property_filter.property_model.fixture_selection = new_selection
                self._invalidate_cache()
                self._refresh_tree()
        self._wizard = None

    def _refresh_tree(self) -> None:
        if self._step_tree is not None:
            self._step_tree.set_name_resolver(self._resolve_node_name)
            self._step_tree.refresh()
        if self._property_pane is not None:
            self._property_pane.refresh_capabilities()

    def _resolve_node_name(self, kind: str, raw_id: str) -> str:
        return resolve_node_name(self._board(), kind, raw_id)

    def _lookup_fixtures(self, node_path: str) -> list:
        model = self._property_filter.property_model if self._property_filter is not None else None
        return lookup_fixtures(self._board(), model, node_path)

    def _refresh_cue_table(self) -> None:
        if self._cue_table is None or self._property_filter is None:
            return
        # Suspend itemChanged so refilling the table doesn't fire rename
        # callbacks for every cell; re-enable after refresh.
        self._cue_table.blockSignals(True)
        try:
            self._cue_table.setRowCount(0)
            for i, cue in enumerate(self._property_filter.property_model.cues):
                self._cue_table.insertRow(i)
                idx_item = QTableWidgetItem(str(i + 1))
                idx_item.setFlags(idx_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._cue_table.setItem(i, 0, idx_item)
                # L19: the Name column is the only editable cell -- Qt handles
                # double-click editing out of the box once ItemIsEditable is set.
                name_item = QTableWidgetItem(cue.name)
                name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self._cue_table.setItem(i, 1, name_item)
                steps_item = QTableWidgetItem(str(len(cue.steps)))
                steps_item.setFlags(steps_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._cue_table.setItem(i, 2, steps_item)
        finally:
            self._cue_table.blockSignals(False)
        self._update_cue_step_button_state()

    def _on_cue_table_item_changed(self, item: QTableWidgetItem) -> None:
        """Persist in-place name edits back into the model (L19)."""
        if self._property_filter is None:
            return
        if item.column() != 1:
            return
        row = item.row()
        cues = self._property_filter.property_model.cues
        if 0 <= row < len(cues):
            new_name = item.text()
            if cues[row].name != new_name:
                cues[row].name = new_name
                self._invalidate_cache()

    def _delete_cue(self) -> None:
        """Remove the currently selected cue from the model (L19)."""
        if self._property_filter is None or self._cue_table is None:
            return
        row = self._cue_table.currentRow()
        cues = self._property_filter.property_model.cues
        if not (0 <= row < len(cues)):
            return
        del cues[row]
        self._invalidate_cache()
        self._refresh_cue_table()
        self._refresh_default_cue_combo()
        if cues:
            self._cue_table.selectRow(min(row, len(cues) - 1))
        else:
            self._apply_cue_selection_state()

    def _delete_step(self) -> None:
        """Remove the currently selected step from the selected cue (L19)."""
        cue = self._selected_cue()
        if cue is None or self._step_tree is None:
            return
        step_idx = self._step_tree.current_step_index()
        if not (0 <= step_idx < len(cue.steps)):
            return
        if len(cue.steps) <= 1:
            logger.info("Refusing to delete the last step of a cue")
            return
        del cue.steps[step_idx]
        self._invalidate_cache()
        self._refresh_cue_table()
        self._step_tree.refresh()

    def _move_cue(self, delta: int) -> None:
        """Move the selected cue up (delta=-1) or down (delta=+1) (L19)."""
        if self._property_filter is None or self._cue_table is None:
            return
        row = self._cue_table.currentRow()
        cues = self._property_filter.property_model.cues
        new_row = row + delta
        if not (0 <= row < len(cues)) or not (0 <= new_row < len(cues)):
            return
        cues[row], cues[new_row] = cues[new_row], cues[row]
        self._invalidate_cache()
        self._refresh_cue_table()
        self._refresh_default_cue_combo()
        self._cue_table.selectRow(new_row)

    def _move_step(self, delta: int) -> None:
        """Move the selected step up (delta=-1) or down (delta=+1) (L19)."""
        cue = self._selected_cue()
        if cue is None or self._step_tree is None:
            return
        step_idx = self._step_tree.current_step_index()
        new_idx = step_idx + delta
        if not (0 <= step_idx < len(cue.steps)) or not (0 <= new_idx < len(cue.steps)):
            return
        cue.steps[step_idx], cue.steps[new_idx] = cue.steps[new_idx], cue.steps[step_idx]
        self._invalidate_cache()
        self._refresh_cue_table()
        self._step_tree.refresh()
        self._step_tree.select_step(
            self._cue_table.currentRow() if self._cue_table is not None else 0,
            new_idx,
        )

    def _update_cue_step_button_state(self) -> None:
        """Enable/disable delete/move buttons based on the current selection."""
        if self._property_filter is None or self._cue_table is None:
            return
        cues = self._property_filter.property_model.cues
        row = self._cue_table.currentRow()
        has_cue = 0 <= row < len(cues)
        for btn in (
            getattr(self, "_delete_cue_button", None),
            getattr(self, "_move_cue_up_button", None),
            getattr(self, "_move_cue_down_button", None),
            getattr(self, "_delete_step_button", None),
            getattr(self, "_move_step_up_button", None),
            getattr(self, "_move_step_down_button", None),
        ):
            if btn is not None:
                btn.setEnabled(has_cue)
        if has_cue:
            if self._move_cue_up_button is not None:
                self._move_cue_up_button.setEnabled(row > 0)
            if self._move_cue_down_button is not None:
                self._move_cue_down_button.setEnabled(row < len(cues) - 1)
            steps = cues[row].steps
            if self._delete_step_button is not None:
                self._delete_step_button.setEnabled(len(steps) > 1)

    def _refresh_default_cue_combo(self) -> None:
        refresh_default_cue_combo(self)

    def _refresh_settings_from_model(self) -> None:
        refresh_settings_from_model(self)

    @override
    def get_channel_list(self) -> list[ExternalChannelDefinition]:
        # Preview channels are published by the compiled vfilter, not the shell.
        return []

    @override
    def _get_configuration(self) -> dict[str, str]:
        if self._property_filter is None:
            return {}
        self._property_filter.serialize()
        return dict(self._property_filter.filter_configurations)

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        if self._property_filter is None:
            return
        self._property_filter.filter_configurations.update(conf)
        self._property_filter.deserialize()
        self._refresh_cue_table()
        self._refresh_default_cue_combo()
        if self._cue_table is not None and self._property_filter.property_model.cues:
            self._cue_table.selectRow(0)
        else:
            self._apply_cue_selection_state()

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {}

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> None:
        return

    @override
    def get_widget(self) -> QWidget:
        return self._root

    @override
    def parent_opened(self) -> None:
        if self._property_filter is not None and not self._property_filter.property_model.fixture_selection.entries:
            self._launch_wizard()
        if self._preview_controller is None:
            return
        self._preview_prompt = YesNoDialog(
            self.get_widget(), "Preview", "Would you like to switch to live preview?",
            self._start_preview,
        )

    # ------------------------------------------------------------------
    # L11 — preview position tracking and XTouch transport integration
    # ------------------------------------------------------------------

    def _preview_push_current_selection(self) -> None:
        """Push the current cue/step selection into the preview controller as the playhead.

        Called when the user picks a cue in the table or a step in the tree.
        Keeps the preview's timeline anchored to what the user is editing so
        pressing PLAY on the XTouch picks up at the authored location.
        """
        if self._preview_controller is None:
            return
        cue_idx = self._cue_table.currentRow() if self._cue_table is not None else -1
        if cue_idx < 0:
            return
        self._preview_controller.set_cue_index(cue_idx)
        step_idx = self._step_tree.current_step_index() if self._step_tree is not None else 0
        if step_idx < 0:
            step_idx = 0
        self._preview_controller.set_timecode(self._step_start_seconds(cue_idx, step_idx))

    def _step_start_seconds(self, cue_idx: int, step_idx: int) -> float:
        """Return the absolute (within-cue) start time in seconds of step ``step_idx``."""
        if self._property_filter is None:
            return 0.0
        cues = self._property_filter.property_model.cues
        if not (0 <= cue_idx < len(cues)):
            return 0.0
        total = 0
        for i, step in enumerate(cues[cue_idx].steps):
            if i >= step_idx:
                break
            total += int(step.duration_40hz)
        return total / 40.0

    def _xtouch_play_pressed(self) -> None:
        """Handle the XTouch play button: toggle play/pause."""
        if self._preview_controller is None or not self._preview_active:
            return
        now_playing = self._preview_controller.toggle_playing()
        self._set_media_button_leds(preview_active=True, playing=now_playing)

    def _xtouch_stop_pressed(self) -> None:
        """Handle the XTouch stop button: pause and rewind to cue 0 step 0 timecode 0."""
        if self._preview_controller is None or not self._preview_active:
            return
        self._preview_controller.rewind_to_start()
        if self._cue_table is not None and self._cue_table.rowCount() > 0:
            self._cue_table.selectRow(0)
        self._set_media_button_leds(preview_active=True, playing=False)

    def _xtouch_forward_pressed(self) -> None:
        """Handle the XTouch FF button: advance one step (wrap into next cue if needed)."""
        if self._preview_controller is None or not self._preview_active or self._property_filter is None:
            return
        cues = self._property_filter.property_model.cues
        if not cues:
            return
        cue_idx = self._preview_controller.cue_index
        step_idx = self._step_tree.current_step_index() if self._step_tree is not None else 0
        if not (0 <= cue_idx < len(cues)):
            return
        if step_idx + 1 < len(cues[cue_idx].steps):
            self._preview_select(cue_idx, step_idx + 1)
        elif cue_idx + 1 < len(cues):
            self._preview_select(cue_idx + 1, 0)

    def _xtouch_rev_pressed(self) -> None:
        """Handle the XTouch REV button: back one step (wrap into previous cue if needed)."""
        if self._preview_controller is None or not self._preview_active or self._property_filter is None:
            return
        cues = self._property_filter.property_model.cues
        if not cues:
            return
        cue_idx = self._preview_controller.cue_index
        step_idx = self._step_tree.current_step_index() if self._step_tree is not None else 0
        if step_idx > 0:
            self._preview_select(cue_idx, step_idx - 1)
        elif cue_idx > 0:
            prev_cue = cue_idx - 1
            last_step = max(0, len(cues[prev_cue].steps) - 1)
            self._preview_select(prev_cue, last_step)

    def _preview_select(self, cue_idx: int, step_idx: int) -> None:
        """Move the editor selection (and preview playhead) to (cue_idx, step_idx)."""
        if self._cue_table is not None and 0 <= cue_idx < self._cue_table.rowCount():
            self._cue_table.selectRow(cue_idx)
        if self._step_tree is not None:
            self._step_tree.select_step(cue_idx, step_idx)
        if self._preview_controller is not None:
            self._preview_controller.set_cue_index(cue_idx)
            self._preview_controller.set_timecode(self._step_start_seconds(cue_idx, step_idx))

    def _set_media_button_leds(self, preview_active: bool, playing: bool = False) -> None:
        """Light / extinguish the XTouch media button LEDs for the preview state.

        PLAY glows solid when the preview is idle and blinks while playing so
        the user can tell play-vs-pause at a glance. STOP, FF and REV glow
        solid whenever preview is active; RECORD stays off (not used).
        """
        from controller.network import NetworkManager
        from proto import Console_pb2  # local import so headless unit tests don't need proto

        if preview_active:
            play_state = (
                Console_pb2.BS_SET_LED_BLINKING if playing else Console_pb2.BS_ACTIVE
            )
            transport_state = Console_pb2.BS_ACTIVE
        else:
            play_state = Console_pb2.BS_SET_LED_NOT_ACTIVE
            transport_state = Console_pb2.BS_SET_LED_NOT_ACTIVE

        # NetworkManager is a QObject singleton; headless tests may not
        # initialise it, so guard against both construction failure and a
        # missing socket interface.
        try:
            nm = NetworkManager()
        except Exception as exc:
            logger.debug("Skipping XTouch LED update (no NetworkManager): %s", exc)
            return
        for button, state in (
            (Console_pb2.BTN_PLAY_RUNCUE, play_state),
            (Console_pb2.BTN_STOP_STOPCUE, transport_state),
            (Console_pb2.BTN_FF_NEXTCUE, transport_state),
            (Console_pb2.BTN_REV_LASTCUE, transport_state),
        ):
            nm.button_msg_to_x_touch(
                Console_pb2.button_state_change(button=button, new_state=state),
            )

    def _connect_xtouch_broadcaster(self) -> None:
        """Subscribe the preview's play/stop/forward/rev handlers to the broadcaster."""
        from model.broadcaster import Broadcaster
        bc = Broadcaster()
        bc.desk_media_play_pressed.connect(self._xtouch_play_pressed)
        bc.desk_media_stop_pressed.connect(self._xtouch_stop_pressed)
        bc.desk_media_forward_pressed.connect(self._xtouch_forward_pressed)
        bc.desk_media_rev_pressed.connect(self._xtouch_rev_pressed)

    def _disconnect_xtouch_broadcaster(self) -> None:
        """Unsubscribe from the broadcaster so a closed editor stops receiving XTouch events."""
        from model.broadcaster import Broadcaster
        bc = Broadcaster()
        for sig, slot in (
            (bc.desk_media_play_pressed, self._xtouch_play_pressed),
            (bc.desk_media_stop_pressed, self._xtouch_stop_pressed),
            (bc.desk_media_forward_pressed, self._xtouch_forward_pressed),
            (bc.desk_media_rev_pressed, self._xtouch_rev_pressed),
        ):
            try:
                sig.disconnect(slot)
            except (TypeError, RuntimeError):
                pass

    @override
    def _update_terminals(self, filter_node: FilterNode) -> None:
        """No-op override: the property-cue vfilter owns its own output signature.

        The base-class :meth:`PreviewEditWidget._update_terminals` compares the
        vfilter's current pyqtgraph outputs to ``self.channels`` (sourced from
        :meth:`get_channel_list`) and removes every terminal not in that list.
        :class:`PropertyCueEditor` returns ``[]`` from :meth:`get_channel_list`
        -- its outputs come from the compiled :class:`PropertyCueFilterModel`,
        not from a user-curated preview-channel list -- so letting the base
        run would strip every output on dialog close and cascade pyqtgraph
        disconnects that blank every peer's ``channel_links``.
        :meth:`FilterNode.update_node_after_settings_changed` (reached later via
        ``super().parent_closed``) performs the correct sync by diffing the
        pyqtgraph terminals against :attr:`out_data_types` from the vfilter's
        own ``_rebuild_io``, so there is nothing for this override to do.
        """

    @override
    def parent_closed(self, filter_node: FilterNode) -> None:
        self._stop_preview()
        # ``NodeEditorFilterConfigWidget.parent_closed`` (reached via super)
        # calls ``filter_node.update_node_after_settings_changed()``, which in
        # turn triggers :meth:`PropertyBasedCueFilter._rebuild_io` -- that's
        # where the vfilter populates ``out_data_types`` from the current
        # property model so the node grows the configured output terminals.
        super().parent_closed(filter_node)

    def _toggle_preview(self) -> None:
        if self._preview_active:
            self._stop_preview()
        else:
            self._start_preview()

    def _start_preview(self) -> None:
        if self._preview_controller is None or self._preview_button is None or self._preview_active:
            return
        # Playback starts paused: the XTouch PLAY button toggles it on;
        # starting playing immediately would make the user chase their own
        # cursor before they've chosen a step to listen to.
        self._preview_controller.set_playing(False)
        # ``start`` builds the ``PREVIEW_CONST`` filters, installs the
        # virtual_name → ``PREVIEW_CONST:value`` mapping on the vfilter and
        # flips ``in_preview_mode = True``. Fish needs to see the show with
        # those constants as scene filters before the preview thread starts
        # pumping GUI updates addressed to them, otherwise every tick triggers
        # ``The requested scene does not contain the requested filter
        # 'Property Cues.0__PREVIEW_CONST__...'`` on the fish side.
        self._preview_controller.start()
        self._transmit_scene_to_fish()
        self._preview_active = True
        self._preview_button.setText("Stop preview")
        # Anchor the preview playhead to whatever the user currently has
        # selected in the cue/step panes, then light the XTouch media
        # buttons and subscribe to their events.
        self._preview_push_current_selection()
        self._connect_xtouch_broadcaster()
        self._set_media_button_leds(preview_active=True, playing=False)

    def _stop_preview(self) -> None:
        if self._preview_controller is None:
            return
        was_active = self._preview_active
        self._preview_controller.stop()
        self._preview_active = False
        if was_active:
            self._set_media_button_leds(preview_active=False)
            self._disconnect_xtouch_broadcaster()
        if self._preview_button is not None:
            self._preview_button.setText("Start preview")
        if was_active:
            # The vfilter is back to non-preview mode; re-transmit so fish
            # drops the ``PREVIEW_CONST`` filters and picks the real native
            # cue filter back up before the user runs a normal cue.
            self._transmit_scene_to_fish()

    def _transmit_scene_to_fish(self) -> None:
        """Re-send the show after flipping the vfilter's preview mode on or off."""
        if self._property_filter is None:
            return
        scene = getattr(self._property_filter, "scene", None)
        board = getattr(scene, "board_configuration", None) if scene is not None else None
        if board is None:
            return
        from controller.file.transmitting_to_fish import transmit_to_fish
        transmit_to_fish(board, False)
