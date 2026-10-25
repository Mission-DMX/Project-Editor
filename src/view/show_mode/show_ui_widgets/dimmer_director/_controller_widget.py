"""Runtime grid controller for the Dimmer Director filter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from model.filters.dimmer_director import EffectCurveMode
from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

if TYPE_CHECKING:
    from model.filters.dimmer_director import DimmerDirectorFilter
    from model.media_assets.image import AbstractImageAsset

_BUTTON_SIZE = 64
_LABEL_WIDTH = 100
_APPLY_COLUMN_TEXT = "🠋"
_PLAY_TEXT = "▶"
_PAUSE_TEXT = "⏸︎"


class ControllerWidget(QWidget):
    """Button grid letting the operator select effect/dimmer curves per group."""

    update_requested = Signal()

    def __init__(
        self,
        model: DimmerDirectorFilter,
        update_list: list[tuple[str, str]] | None,
        feedback_enabled: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """Build the grid, wire buttons and connect feedback handling if enabled."""
        super().__init__(parent)
        self._model = model
        self._update_list = update_list
        self._feedback_enabled = feedback_enabled
        self._effect_apply_all_buttons: list[QPushButton] = []
        self._dimmer_apply_all_buttons: list[QPushButton] = []
        self._effect_cell_buttons: list[list[QPushButton]] = []
        self._dimmer_cell_buttons: list[list[QPushButton]] = []
        self._play_pause_buttons: list[QPushButton] = []
        self._group_names: list[str] = [g.name for g in model.groups]
        self._effect_count = len(model.effect_curves)
        self._dimmer_count = len(model.dimmer_curves)
        self._layout = QGridLayout()
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._build_grid()
        self.setLayout(self._layout)
        self._refresh_feedback_state()
        self._model.configuration_changed.mapped_signal.connect(self._on_model_changed)

    # ------------------------------------------------------------------ build

    def _build_grid(self) -> None:
        """Populate the layout with the recall spinbox, header row and group rows."""
        self._recall_sp = JogwheelSpinBox()
        if self._update_list is not None:
            self._recall_sp.value_submitted.connect(self._recall_issued)
        recall_count = len(self._model.recalls)
        self._recall_sp.setEnabled(recall_count > 0)
        self._recall_sp.setRange(0, max(recall_count - 1, 0))
        self._recall_sp.setMaximumSize(_LABEL_WIDTH, _BUTTON_SIZE)
        self._layout.addWidget(self._recall_sp, 0, 0)

        effect_curves = self._model.effect_curves
        dimmer_curves = self._model.dimmer_curves

        for i, curve in enumerate(effect_curves):
            btn = QPushButton(_APPLY_COLUMN_TEXT)
            btn.setToolTip(f"Apply effect curve '{curve.name}' to every group.")
            btn.setFixedSize(_BUTTON_SIZE, _BUTTON_SIZE)
            _apply_curve_icon(btn, curve.icon_asset)
            if self._update_list is not None:
                btn.clicked.connect(lambda _checked=False, ii=i: self._apply_effect_column(ii))
            self._effect_apply_all_buttons.append(btn)
            self._layout.addWidget(btn, 0, 1 + i)
        effect_offset = 1 + self._effect_count

        for i, curve in enumerate(dimmer_curves):
            btn = QPushButton(_APPLY_COLUMN_TEXT)
            btn.setToolTip(f"Apply dimmer curve '{curve.name}' to every group.")
            btn.setFixedSize(_BUTTON_SIZE, _BUTTON_SIZE)
            _apply_curve_icon(btn, curve.icon_asset)
            if self._update_list is not None:
                btn.clicked.connect(lambda _checked=False, ii=i: self._apply_dimmer_column(ii))
            self._dimmer_apply_all_buttons.append(btn)
            self._layout.addWidget(btn, 0, effect_offset + i)

        play_col = effect_offset + self._dimmer_count

        for row, group in enumerate(self._model.groups):
            label = QLabel(group.name)
            label.setWordWrap(True)
            label.setFixedWidth(_LABEL_WIDTH)
            label.setMaximumHeight(_BUTTON_SIZE)
            self._layout.addWidget(label, row + 1, 0)

            effect_row: list[QPushButton] = []
            for i, curve in enumerate(effect_curves):
                btn = QPushButton()
                btn.setFixedSize(_BUTTON_SIZE, _BUTTON_SIZE)
                btn.setToolTip(f"{group.name} → effect '{curve.name}'")
                _apply_curve_icon(btn, curve.icon_asset)
                if self._update_list is not None:
                    btn.clicked.connect(
                        lambda _checked=False, g=group.name, ii=i: self._apply_effect_cell(g, ii),
                    )
                effect_row.append(btn)
                self._layout.addWidget(btn, row + 1, 1 + i)
            self._effect_cell_buttons.append(effect_row)

            dimmer_row: list[QPushButton] = []
            for i, curve in enumerate(dimmer_curves):
                btn = QPushButton()
                btn.setFixedSize(_BUTTON_SIZE, _BUTTON_SIZE)
                btn.setToolTip(f"{group.name} → dimmer '{curve.name}'")
                _apply_curve_icon(btn, curve.icon_asset)
                if self._update_list is not None:
                    btn.clicked.connect(
                        lambda _checked=False, g=group.name, ii=i: self._apply_dimmer_cell(g, ii),
                    )
                dimmer_row.append(btn)
                self._layout.addWidget(btn, row + 1, effect_offset + i)
            self._dimmer_cell_buttons.append(dimmer_row)

            play_btn = QPushButton(_PAUSE_TEXT)
            play_btn.setFixedSize(_BUTTON_SIZE, _BUTTON_SIZE)
            play_btn.setToolTip(f"Toggle playback of '{group.name}'.")
            play_btn.setCheckable(True)
            if self._update_list is not None:
                play_btn.clicked.connect(lambda _checked=False, g=group.name: self._toggle_play(g))
            self._play_pause_buttons.append(play_btn)
            self._layout.addWidget(play_btn, row + 1, play_col)

    # -------------------------------------------------------------- clicks

    def _apply_effect_column(self, effect_index: int) -> None:
        """Enqueue updates that switch every group to the given effect curve."""
        if self._update_list is None:
            return
        self._update_list.clear()
        for name in self._group_names:
            self._update_list.append(self._model.get_update_msg_for_effect_change(name, effect_index))
        self.update_requested.emit()

    def _apply_dimmer_column(self, dimmer_index: int) -> None:
        """Enqueue updates that switch every group to the given dimmer curve."""
        if self._update_list is None:
            return
        self._update_list.clear()
        for name in self._group_names:
            self._update_list.append(self._model.get_update_msg_for_dimmer_change(name, dimmer_index))
        self.update_requested.emit()

    def _apply_effect_cell(self, group_name: str, effect_index: int) -> None:
        """Enqueue an effect-curve switch for one group."""
        if self._update_list is None:
            return
        self._update_list.append(self._model.get_update_msg_for_effect_change(group_name, effect_index))
        self.update_requested.emit()

    def _apply_dimmer_cell(self, group_name: str, dimmer_index: int) -> None:
        """Enqueue a dimmer-curve switch for one group."""
        if self._update_list is None:
            return
        self._update_list.append(self._model.get_update_msg_for_dimmer_change(group_name, dimmer_index))
        self.update_requested.emit()

    def _toggle_play(self, group_name: str) -> None:
        """Enqueue a pause or resume depending on the current paused state."""
        if self._update_list is None:
            return
        group_index = self._group_names.index(group_name) if group_name in self._group_names else -1
        if group_index < 0:
            return
        paused_states = self._model.get_group_paused_states()
        paused = paused_states[group_index] if group_index < len(paused_states) else False
        if paused:
            self._update_list.append(self._model.get_update_msg_for_resume(group_name))
        else:
            self._update_list.append(self._model.get_update_msg_for_pause(group_name))
        self.update_requested.emit()

    def _recall_issued(self, recall_index: int) -> None:
        """Enqueue the recall's full selection as one batch of updates."""
        if self._update_list is None:
            return
        recalls = self._model.recalls
        if not 0 <= recall_index < len(recalls):
            return
        selections = recalls[recall_index].selections
        self._update_list.clear()
        for group_idx, (eff, dim) in enumerate(selections):
            if group_idx >= len(self._group_names):
                break
            name = self._group_names[group_idx]
            self._update_list.append(self._model.get_update_msg_for_effect_change(name, eff))
            self._update_list.append(self._model.get_update_msg_for_dimmer_change(name, dim))
        self.update_requested.emit()

    # -------------------------------------------------------------- feedback

    def _on_model_changed(self) -> None:
        """Pick up external configuration changes that affect the shown buttons."""
        self._refresh_feedback_state()

    def _refresh_feedback_state(self) -> None:
        """Sync the pressed/disabled state of all buttons with the model's feedback state."""
        active_effects = self._model.get_active_effect_indices()
        active_dimmers = self._model.get_active_dimmer_indices()
        paused_states = self._model.get_group_paused_states()
        effect_curves = self._model.effect_curves
        if self._feedback_enabled:
            for row, row_buttons in enumerate(self._effect_cell_buttons):
                active = active_effects[row] if row < len(active_effects) else -1
                for i, btn in enumerate(row_buttons):
                    btn.setDown(i == active)
            for row, row_buttons in enumerate(self._dimmer_cell_buttons):
                active = active_dimmers[row] if row < len(active_dimmers) else -1
                for i, btn in enumerate(row_buttons):
                    btn.setDown(i == active)
        for row, btn in enumerate(self._play_pause_buttons):
            active = active_effects[row] if row < len(active_effects) else 0
            paused = paused_states[row] if row < len(paused_states) else False
            if 0 <= active < len(effect_curves):
                is_repeat = effect_curves[active].mode == EffectCurveMode.REPEAT
            else:
                is_repeat = False
            btn.setEnabled(is_repeat and self._update_list is not None)
            btn.blockSignals(True)
            btn.setChecked(paused)
            btn.setText(_PLAY_TEXT if paused else _PAUSE_TEXT)
            btn.blockSignals(False)


def _apply_curve_icon(button: QPushButton, asset: AbstractImageAsset | None) -> None:
    """Set the button's icon from the configured image asset, if any."""
    if asset is None:
        return
    try:
        image = asset.get_image_for_ui()
    except Exception:
        return
    if image is None:
        return
    pixmap = QPixmap.fromImage(image)
    if pixmap.isNull():
        return
    button.setIcon(QIcon(pixmap))
    button.setIconSize(button.size() * 0.75)
