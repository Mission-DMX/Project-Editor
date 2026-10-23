"""QDialog for creating/editing effect presets.

The keyframe editor is implemented as a plain ``QTableWidget`` rather than
reusing ``TimelineContainer``. The timeline container is tightly coupled to
the ``Cue``/``BankSet`` runtime (desk columns, live preview, etc.) and surfacing
a stand-alone keyframe-expression authoring experience through it would require
a substantial stubbing effort. For WP13 we author the per-channel expression
strings directly in a simple table: that keeps the dialog self-contained and
matches the preset JSON structure one-for-one. The dialog accepts dialed-in
literal numbers and translates them to literal expression strings on save.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from model.virtual_filters.property_cues.presets import (
    EffectPreset,
    PresetHintSpec,
    PresetHintType,
    PresetKeyFrameEntry,
)
from model.virtual_filters.property_cues.presets.schema import validate
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

_APPLIES_FOR_CHOICES = ("dimmer", "position", "colour", "gobo", "beam", "focus", "frost")
_HINT_TYPE_CHOICES = ("float", "int", "color")

_PROPERTY_CHANNELS: dict[str, tuple[str, ...]] = {
    "dimmer": ("brightness", "strobefreq", "duty_cycle"),
    "position": ("pan_value", "pan_curvesel", "tilt_value", "tilt_curvesel"),
    "colour": ("color",),
    "beam": ("focus", "zoom", "iris"),
    "focus": ("focus",),
    "gobo": ("goboslot_0", "goborotation_0"),
    "frost": ("frost_intensity",),
}

_DEFAULT_USER_SUBDIR = "cuepresets"
_USER_STORAGE_DIRECTORY_MODE = 0o770


class PresetEditorDialog(QDialog):
    """Dialog for authoring :class:`EffectPreset` instances."""

    def __init__(self, existing: EffectPreset | None = None,
                 user_dir: Path | None = None, parent: QWidget | None = None) -> None:
        """Open the dialog, optionally pre-populated with ``existing``.

        Modifications are always written below ``user_dir`` (defaulting to the
        standard missionDMX user storage sub-directory) so built-in presets are
        never overwritten.
        """
        super().__init__(parent)
        self.setWindowTitle("Edit effect preset")
        self._user_dir = Path(user_dir) if user_dir is not None else self._default_user_dir()
        self._result_preset: EffectPreset | None = None
        self._msgbox: QMessageBox | None = None

        self._applies_combo = QComboBox()
        self._applies_combo.addItems(_APPLIES_FOR_CHOICES)
        self._applies_combo.currentTextChanged.connect(lambda _t: self._rebuild_kf_columns())

        self._name_edit = QLineEdit()
        self._description_edit = QTextEdit()
        self._description_edit.setFixedHeight(60)

        self._hints_table = QTableWidget(0, 6)
        self._hints_table.setHorizontalHeaderLabels(["id", "type", "default", "min", "max", ""])
        self._hints_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._add_hint_button = QPushButton("+ Add hint")
        self._add_hint_button.clicked.connect(lambda: self._add_hint_row())  # noqa: PLW0108 - prevents Qt passing checked bool as hint_id positional

        self._kf_table = QTableWidget(0, 1)
        self._kf_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._add_kf_button = QPushButton("+ Add keyframe")
        self._add_kf_button.clicked.connect(lambda: self._add_kf_row())  # noqa: PLW0108 - prevents Qt passing checked bool as duration_expr positional

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self._buttons.accepted.connect(self._save)
        self._buttons.rejected.connect(self.reject)

        self._build_layout()
        self._rebuild_kf_columns()

        if existing is not None:
            self._populate_from(existing)

    @staticmethod
    def _default_user_dir() -> Path:
        from controller.file.user_data_storage import _USER_STORAGE_PATH
        return _USER_STORAGE_PATH / _DEFAULT_USER_SUBDIR

    def _build_layout(self) -> None:
        root = QVBoxLayout()
        form = QFormLayout()
        form.addRow("Applies for", self._applies_combo)
        form.addRow("Name", self._name_edit)
        form.addRow("Description", self._description_edit)
        root.addLayout(form)

        hints_box = QGroupBox("Hints")
        hints_layout = QVBoxLayout()
        hints_layout.addWidget(self._hints_table)
        hints_layout.addWidget(self._add_hint_button)
        hints_box.setLayout(hints_layout)
        root.addWidget(hints_box)

        kf_box = QGroupBox("Keyframes")
        kf_layout = QVBoxLayout()
        kf_layout.addWidget(QLabel("Enter expression strings (jinja); literals accepted."))
        kf_layout.addWidget(self._kf_table)
        kf_layout.addWidget(self._add_kf_button)
        kf_box.setLayout(kf_layout)
        root.addWidget(kf_box)

        root.addWidget(self._buttons)
        self.setLayout(root)

    def _channels_for_current_property(self) -> tuple[str, ...]:
        return _PROPERTY_CHANNELS.get(self._applies_combo.currentText(), ())

    def _rebuild_kf_columns(self) -> None:
        channels = self._channels_for_current_property()
        headers = ["duration", *channels, ""]
        existing = [(self._kf_table.item(r, 0).text() if self._kf_table.item(r, 0) else "")
                    for r in range(self._kf_table.rowCount())]
        self._kf_table.clear()
        self._kf_table.setColumnCount(len(headers))
        self._kf_table.setHorizontalHeaderLabels(headers)
        self._kf_table.setRowCount(0)
        for duration in existing:
            self._add_kf_row(duration_expr=duration)

    def _add_hint_row(self, hint_id: str = "", hint_type: str = "float",
                      default: str = "0", minimum: str = "", maximum: str = "") -> None:
        row = self._hints_table.rowCount()
        self._hints_table.insertRow(row)
        self._hints_table.setItem(row, 0, QTableWidgetItem(hint_id))
        type_combo = QComboBox()
        type_combo.addItems(_HINT_TYPE_CHOICES)
        if hint_type in _HINT_TYPE_CHOICES:
            type_combo.setCurrentText(hint_type)
        self._hints_table.setCellWidget(row, 1, type_combo)
        default_spin = JogwheelDoubleSpinBox()
        default_spin.setRange(-1000000.0, 1000000.0)
        default_spin.setDecimals(3)
        try:
            default_spin.setValue(float(default))
        except ValueError:
            default_spin.setValue(0.0)
        self._hints_table.setCellWidget(row, 2, default_spin)
        self._hints_table.setCellWidget(row, 3, self._make_optional_edit(minimum))
        self._hints_table.setCellWidget(row, 4, self._make_optional_edit(maximum))
        remove_btn = QPushButton("x")
        remove_btn.clicked.connect(lambda _checked=False, b=remove_btn: self._remove_row(self._hints_table, b))
        self._hints_table.setCellWidget(row, 5, remove_btn)

    @staticmethod
    def _make_optional_edit(value: str) -> QLineEdit:
        edit = QLineEdit(value)
        edit.setPlaceholderText("blank = none")
        return edit

    def _add_kf_row(self, duration_expr: str = "1.0", channel_exprs: dict[str, str] | None = None) -> None:
        row = self._kf_table.rowCount()
        self._kf_table.insertRow(row)
        self._kf_table.setItem(row, 0, QTableWidgetItem(duration_expr))
        channels = self._channels_for_current_property()
        for col, channel in enumerate(channels, start=1):
            value = (channel_exprs or {}).get(channel, "0")
            self._kf_table.setItem(row, col, QTableWidgetItem(value))
        remove_btn = QPushButton("x")
        remove_btn.clicked.connect(lambda _checked=False, b=remove_btn: self._remove_row(self._kf_table, b))
        self._kf_table.setCellWidget(row, len(channels) + 1, remove_btn)

    @staticmethod
    def _remove_row(table: QTableWidget, button: QPushButton) -> None:
        for row in range(table.rowCount()):
            if table.cellWidget(row, table.columnCount() - 1) is button:
                table.removeRow(row)
                return

    def _populate_from(self, preset: EffectPreset) -> None:
        if preset.applies_for in _APPLIES_FOR_CHOICES:
            self._applies_combo.setCurrentText(preset.applies_for)
        self._name_edit.setText(preset.name)
        self._description_edit.setPlainText(preset.description)
        for hint in preset.hints:
            self._add_hint_row(
                hint_id=hint.id,
                hint_type=hint.type.value,
                default=str(hint.default),
                minimum="" if hint.minimum is None else str(hint.minimum),
                maximum="" if hint.maximum is None else str(hint.maximum),
            )
        self._rebuild_kf_columns()
        self._kf_table.setRowCount(0)
        for entry in preset.kf_requests:
            self._add_kf_row(duration_expr=entry.duration_expr, channel_exprs=entry.channel_exprs)

    def _collect_hints_blob(self) -> list[dict]:
        out: list[dict] = []
        for row in range(self._hints_table.rowCount()):
            id_item = self._hints_table.item(row, 0)
            type_combo = self._hints_table.cellWidget(row, 1)
            default_spin = self._hints_table.cellWidget(row, 2)
            type_name = type_combo.currentText() if isinstance(type_combo, QComboBox) else "float"
            default_value = default_spin.value() if isinstance(default_spin, JogwheelDoubleSpinBox) else 0.0
            hint: dict = {
                "id": id_item.text() if id_item else "",
                "type": type_name,
                "default": int(default_value) if type_name == "int" else (
                    str(default_value) if type_name == "color" else float(default_value)
                ),
            }
            for key, col in (("min", 3), ("max", 4)):
                val = self._read_optional_number(self._hints_table.cellWidget(row, col))
                if val is not None:
                    hint[key] = val
            out.append(hint)
        return out

    @staticmethod
    def _read_optional_number(edit: QWidget | None) -> float | None:
        if not isinstance(edit, QLineEdit):
            return None
        text = edit.text().strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _collect_kf_blob(self) -> list[dict]:
        out: list[dict] = []
        channels = self._channels_for_current_property()
        for row in range(self._kf_table.rowCount()):
            duration_item = self._kf_table.item(row, 0)
            duration = duration_item.text() if duration_item else ""
            channel_exprs: dict[str, str] = {}
            for col, channel in enumerate(channels, start=1):
                cell = self._kf_table.item(row, col)
                channel_exprs[channel] = cell.text() if cell else ""
            out.append({"duration": duration, "channels": channel_exprs})
        return out

    def _save(self) -> None:
        name = self._name_edit.text().strip()
        blob = {
            "name": name,
            "description": self._description_edit.toPlainText(),
            "applies_for": self._applies_combo.currentText(),
            "hints": self._collect_hints_blob(),
            "kf_requests": self._collect_kf_blob(),
        }
        errors = validate(blob)
        if not name:
            errors.insert(0, "Preset name must not be empty.")
        if errors:
            self._show_validation_errors(errors)
            return
        try:
            self._user_dir.mkdir(parents=True, mode=_USER_STORAGE_DIRECTORY_MODE, exist_ok=True)
        except OSError as exc:
            self._show_validation_errors([f"Could not create user directory: {exc}"])
            return
        target_path = self._user_dir / f"{name}.json"
        try:
            target_path.write_text(json.dumps(blob, indent=2), encoding="utf-8")
        except OSError as exc:
            self._show_validation_errors([f"Could not write preset file: {exc}"])
            return
        hints = tuple(PresetHintSpec(id=h["id"], type=PresetHintType(h["type"]), default=h["default"],
                                     minimum=h.get("min"), maximum=h.get("max")) for h in blob["hints"])
        kf = tuple(PresetKeyFrameEntry(duration_expr=e["duration"], channel_exprs=dict(e["channels"]))
                   for e in blob["kf_requests"])
        self._result_preset = EffectPreset(
            name=name, description=blob["description"], applies_for=blob["applies_for"],
            hints=hints, kf_requests=kf, source_path=str(target_path), is_builtin=False,
        )
        self.accept()

    def _show_validation_errors(self, errors: list[str]) -> None:
        self._msgbox = QMessageBox(self)
        self._msgbox.setIcon(QMessageBox.Icon.Warning)
        self._msgbox.setWindowTitle("Preset validation failed")
        self._msgbox.setText("The preset could not be saved.")
        self._msgbox.setDetailedText("\n".join(errors))
        self._msgbox.setStandardButtons(QMessageBox.StandardButton.Ok)
        self._msgbox.show()

    def result_preset(self) -> EffectPreset | None:
        """Return the authored preset, or None if the dialog was cancelled."""
        return self._result_preset
