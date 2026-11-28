"""QDialog for creating/editing effect presets.

The keyframe editor is implemented as a plain ``QTableWidget`` rather than
reusing ``TimelineContainer``. The timeline container is tightly coupled to
the ``Cue``/``BankSet`` runtime (desk columns, live preview, etc.) and surfacing
a stand-alone keyframe-expression authoring experience through it would require
a substantial stubbing effort. Per-channel expression strings are authored
directly in a simple table that matches the preset JSON structure
one-for-one; dialed-in literal numbers get written as literal expression
strings on save.
"""

from __future__ import annotations

import json
import re
from logging import getLogger
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

from model.filters._channel_names import sanitize_channel_name
from model.virtual_filters.property_cues._property_registry import (
    preset_channels_for,
    properties_in_order,
)
from model.virtual_filters.property_cues.presets import (
    EffectPreset,
    PresetHintSpec,
    PresetHintType,
    PresetKeyFrameEntry,
    reload_preset_library,
)
from model.virtual_filters.property_cues.presets.schema import validate
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox, JogwheelSpinBox

logger = getLogger(__name__)

# the "Applies for" choices and the per-property preset channel columns
# derive from :data:`_property_registry.REGISTRY` so there is no second table
# to keep in sync with the compiler.
_APPLIES_FOR_CHOICES = tuple(e.id for e in properties_in_order())
_HINT_TYPE_CHOICES = ("float", "int", "color")

# Populated from the registry at import time; kept as a dict for subscript-style
# access by existing readers (tests, debugger utilities).
_PROPERTY_CHANNELS: dict[str, tuple[str, ...]] = {
    e.id: preset_channels_for(e.id) for e in properties_in_order()
}

_DEFAULT_USER_SUBDIR = "cuepresets"
_USER_STORAGE_DIRECTORY_MODE = 0o770

# Allow only characters safe on all common filesystems for preset filenames.
# Anything outside the allow-list is dropped during sanitisation.
_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize_filename(name: str) -> str:
    """Return a filename-safe form of ``name``.

    Uses the shared channel-name sanitiser to normalise visible whitespace
    and separator characters, then strips any remaining characters that are
    unsafe on common filesystems. The returned string is never empty.
    """
    base = _FILENAME_SAFE.sub("_", sanitize_channel_name(name)).strip("._-")
    return base or "preset"


def _build_hint_default_widget(hint_type: str, default: str) -> QWidget:
    """Return the editor widget appropriate for a hint's default value.

    colour hints get a plain :class:`QLineEdit` so ``"0,0,0"`` round-trips
    unchanged; int hints get :class:`JogwheelSpinBox`; float hints get the
    original :class:`JogwheelDoubleSpinBox`.
    """
    if hint_type == "color":
        line = QLineEdit(default)
        line.setPlaceholderText("H,S,I")
        return line
    if hint_type == "int":
        spin_i = JogwheelSpinBox()
        spin_i.setRange(-1_000_000, 1_000_000)
        try:
            spin_i.setValue(int(float(default)) if default else 0)
        except (TypeError, ValueError):
            spin_i.setValue(0)
        return spin_i
    spin_f = JogwheelDoubleSpinBox()
    spin_f.setRange(-1_000_000.0, 1_000_000.0)
    spin_f.setDecimals(3)
    try:
        spin_f.setValue(float(default) if default else 0.0)
    except (TypeError, ValueError):
        spin_f.setValue(0.0)
    return spin_f


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
        # track the original filename when editing so a rename can
        # delete the stale file instead of orphaning it alongside the new one.
        self._original_source_path: Path | None = None
        # ``_rebuild_kf_columns`` is wired to the "Applies for" combo's
        # change signal and also runs after :meth:`_populate_from` inserts
        # preset-specific rows. Suppress the rebuild while populating so
        # colour defaults don't get coerced through the float spin box.
        self._populating = False

        self._applies_combo = QComboBox()
        self._applies_combo.addItems(_APPLIES_FOR_CHOICES)
        self._applies_combo.currentTextChanged.connect(self._on_applies_changed)

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

    def _on_applies_changed(self, _text: str) -> None:
        """Rebuild the keyframe columns when the user changes the ``applies_for`` type.

        No-op while :meth:`_populate_from` is seeding the dialog so the
        initial populate -> rebuild -> populate cycle does not clobber
        the expressions we just loaded.
        """
        if self._populating:
            return
        self._rebuild_kf_columns()

    def _snapshot_kf_rows(self) -> list[dict[str, str]]:
        """Capture ``{header: cell_text}`` for every row in the keyframe table."""
        headers = [
            self._kf_table.horizontalHeaderItem(c).text() if self._kf_table.horizontalHeaderItem(c) else ""
            for c in range(self._kf_table.columnCount())
        ]
        rows: list[dict[str, str]] = []
        for r in range(self._kf_table.rowCount()):
            snapshot: dict[str, str] = {}
            for c, header in enumerate(headers):
                if not header or header == "duration":
                    continue
                cell = self._kf_table.item(r, c)
                if cell is not None:
                    snapshot[header] = cell.text()
            rows.append(snapshot)
        return rows

    def _rebuild_kf_columns(self) -> None:
        """Rebuild the keyframe table columns for the current applies_for.

        a prior snapshot of per-channel expressions is carried across
        the rebuild so switching ``applies_for`` back and forth does not
        drop the user's authored expressions. Unknown channels (ones the
        new applies_for doesn't expose) are preserved in
        ``self._passthrough_rows`` and written back on save so round-
        tripping an existing preset doesn't lose any data.
        """
        channels = self._channels_for_current_property()
        headers = ["duration", *channels, ""]
        prior_rows = self._snapshot_kf_rows()
        prior_passthrough = list(getattr(self, "_passthrough_rows", []))
        prior_durations = [
            self._kf_table.item(r, 0).text() if self._kf_table.item(r, 0) else ""
            for r in range(self._kf_table.rowCount())
        ]
        self._kf_table.clear()
        self._kf_table.setColumnCount(len(headers))
        self._kf_table.setHorizontalHeaderLabels(headers)
        self._kf_table.setRowCount(0)
        # Carry the unknown channels forward so they are written back on
        # save; one entry per existing row. ``_passthrough_rows`` is keyed
        # by row index.
        self._passthrough_rows: list[dict[str, str]] = []
        for i, duration in enumerate(prior_durations):
            # Combine the currently-displayed row with the previous
            # passthrough map so expressions we already couldn't show get
            # considered again under the new applies_for.
            combined: dict[str, str] = {}
            combined.update(prior_rows[i] if i < len(prior_rows) else {})
            if i < len(prior_passthrough):
                combined.update(prior_passthrough[i])
            known_exprs = {k: v for k, v in combined.items() if k in channels}
            passthrough = {k: v for k, v in combined.items() if k not in channels}
            self._add_kf_row(
                duration_expr=duration,
                channel_exprs=known_exprs,
                passthrough=passthrough,
            )

    def _add_hint_row(self, hint_id: str = "", hint_type: str = "float",
                      default: str = "0", minimum: str = "", maximum: str = "") -> None:
        row = self._hints_table.rowCount()
        self._hints_table.insertRow(row)
        self._hints_table.setItem(row, 0, QTableWidgetItem(hint_id))
        type_combo = QComboBox()
        type_combo.addItems(_HINT_TYPE_CHOICES)
        if hint_type in _HINT_TYPE_CHOICES:
            type_combo.setCurrentText(hint_type)
        else:
            hint_type = "float"
        self._hints_table.setCellWidget(row, 1, type_combo)
        # honour the hint's declared type when choosing the default
        # widget. The old code always used a float spin box, so a colour
        # hint's ``"0,0,0"`` default was coerced to ``0.0`` on load and the
        # preset silently lost its colour information.
        self._hints_table.setCellWidget(
            row, 2, _build_hint_default_widget(hint_type, default),
        )
        type_combo.currentTextChanged.connect(
            lambda new_type, r=row: self._on_hint_type_changed(r, new_type),
        )
        self._hints_table.setCellWidget(row, 3, self._make_optional_edit(minimum))
        self._hints_table.setCellWidget(row, 4, self._make_optional_edit(maximum))
        remove_btn = QPushButton("x")
        remove_btn.clicked.connect(lambda _checked=False, b=remove_btn: self._remove_hint_row(self._hints_table, b))
        self._hints_table.setCellWidget(row, 5, remove_btn)

    def _on_hint_type_changed(self, row: int, new_type: str) -> None:
        """Swap the default widget when the user changes a hint's type.

        Preserves whatever representation the previous widget had (best
        effort: colour string stays colour-ish, numeric stays numeric).
        """
        if row >= self._hints_table.rowCount():
            return
        current = self._hints_table.cellWidget(row, 2)
        prior_value = ""
        if isinstance(current, (JogwheelDoubleSpinBox, JogwheelSpinBox)):
            prior_value = str(current.value())
        elif isinstance(current, QLineEdit):
            prior_value = current.text()
        self._hints_table.setCellWidget(
            row, 2, _build_hint_default_widget(new_type, prior_value),
        )

    @staticmethod
    def _make_optional_edit(value: str) -> QLineEdit:
        edit = QLineEdit(value)
        edit.setPlaceholderText("blank = none")
        return edit

    def _add_kf_row(
        self, duration_expr: str = "1.0",
        channel_exprs: dict[str, str] | None = None,
        passthrough: dict[str, str] | None = None,
    ) -> None:
        row = self._kf_table.rowCount()
        self._kf_table.insertRow(row)
        self._kf_table.setItem(row, 0, QTableWidgetItem(duration_expr))
        channels = self._channels_for_current_property()
        for col, channel in enumerate(channels, start=1):
            value = (channel_exprs or {}).get(channel, "0")
            self._kf_table.setItem(row, col, QTableWidgetItem(value))
        remove_btn = QPushButton("x")
        remove_btn.clicked.connect(lambda _checked=False, b=remove_btn: self._remove_row(b))
        self._kf_table.setCellWidget(row, len(channels) + 1, remove_btn)
        # keep ``_passthrough_rows`` in step with the kf_table so
        # unknown-channel expressions (ones the dialog's columns don't show
        # but the loaded preset carried) round-trip through save.
        if not hasattr(self, "_passthrough_rows"):
            self._passthrough_rows = []
        while len(self._passthrough_rows) < row:
            self._passthrough_rows.append({})
        if len(self._passthrough_rows) == row:
            self._passthrough_rows.append(dict(passthrough or {}))
        else:
            self._passthrough_rows[row] = dict(passthrough or {})

    def _remove_row(self, button: QPushButton) -> None:
        table = self._kf_table
        for row in range(table.rowCount()):
            if table.cellWidget(row, table.columnCount() - 1) is button:
                table.removeRow(row)
                if hasattr(self, "_passthrough_rows") and row < len(self._passthrough_rows):
                    del self._passthrough_rows[row]
                return

    @staticmethod
    def _remove_hint_row(table: QTableWidget, button: QPushButton) -> None:
        for row in range(table.rowCount()):
            if table.cellWidget(row, table.columnCount() - 1) is button:
                table.removeRow(row)
                return

    def _populate_from(self, preset: EffectPreset) -> None:
        # suppress rebuild side effects while filling the dialog --
        # the setCurrentText call below would otherwise trigger
        # ``_on_applies_changed`` -> ``_rebuild_kf_columns`` and clobber the
        # just-cleared ``_passthrough_rows``.
        self._populating = True
        try:
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
            # Record the source path so a rename on save can delete the stale
            # file -- but only for user-authored presets. Built-in presets
            # live elsewhere (shipped alongside the editor) and must never
            # be touched: the user's rename always writes a fresh copy to
            # the user dir.
            if preset.source_path and not preset.is_builtin:
                self._original_source_path = Path(preset.source_path)
            self._rebuild_kf_columns()
            self._kf_table.setRowCount(0)
            self._passthrough_rows = []
            channels = self._channels_for_current_property()
            for entry in preset.kf_requests:
                known = {k: v for k, v in entry.channel_exprs.items() if k in channels}
                passthrough = {k: v for k, v in entry.channel_exprs.items() if k not in channels}
                self._add_kf_row(
                    duration_expr=entry.duration_expr,
                    channel_exprs=known,
                    passthrough=passthrough,
                )
        finally:
            self._populating = False

    def _collect_hints_blob(self) -> list[dict]:
        out: list[dict] = []
        for row in range(self._hints_table.rowCount()):
            id_item = self._hints_table.item(row, 0)
            type_combo = self._hints_table.cellWidget(row, 1)
            default_widget = self._hints_table.cellWidget(row, 2)
            type_name = type_combo.currentText() if isinstance(type_combo, QComboBox) else "float"
            # read the hint's default value in the representation its
            # widget uses so colour defaults don't get coerced to float
            # (``"0.0"``) and ints don't get silently promoted to floats.
            if type_name == "color":
                if isinstance(default_widget, QLineEdit):
                    default_value: int | float | str = default_widget.text()
                else:
                    default_value = "0,0,0"
            elif type_name == "int":
                if isinstance(default_widget, (JogwheelSpinBox, JogwheelDoubleSpinBox)):
                    default_value = int(default_widget.value())
                else:
                    default_value = 0
            else:  # float
                if isinstance(default_widget, (JogwheelDoubleSpinBox, JogwheelSpinBox)):
                    default_value = float(default_widget.value())
                else:
                    default_value = 0.0
            hint: dict = {
                "id": id_item.text() if id_item else "",
                "type": type_name,
                "default": default_value,
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
            # merge any passthrough (unknown-column) channels we
            # captured in :meth:`_populate_from` or during an applies_for
            # swap so they survive the round-trip to disk.
            if hasattr(self, "_passthrough_rows") and row < len(self._passthrough_rows):
                for key, expr in self._passthrough_rows[row].items():
                    channel_exprs.setdefault(key, expr)
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
        # sanitise the filename so names with spaces, slashes or other
        # characters unsafe on the host filesystem don't fail silently.
        safe_name = _sanitize_filename(name)
        target_path = self._user_dir / f"{safe_name}.json"
        try:
            target_path.write_text(json.dumps(blob, indent=2), encoding="utf-8")
        except OSError as exc:
            self._show_validation_errors([f"Could not write preset file: {exc}"])
            return
        # if the user renamed the preset while editing, drop the stale
        # file so we don't accumulate orphaned ``*.json`` files in the user
        # library. Built-in presets live elsewhere and are never touched here.
        if (
            self._original_source_path is not None
            and self._original_source_path.exists()
            and self._original_source_path != target_path
        ):
            try:
                self._original_source_path.unlink()
            except OSError as exc:
                logger.warning(
                    "Could not remove old preset file %s: %s",
                    self._original_source_path, exc,
                )
        hints = tuple(PresetHintSpec(id=h["id"], type=PresetHintType(h["type"]), default=h["default"],
                                     minimum=h.get("min"), maximum=h.get("max")) for h in blob["hints"])
        kf = tuple(PresetKeyFrameEntry(duration_expr=e["duration"], channel_exprs=dict(e["channels"]))
                   for e in blob["kf_requests"])
        self._result_preset = EffectPreset(
            name=name, description=blob["description"], applies_for=blob["applies_for"],
            hints=hints, kf_requests=kf, source_path=str(target_path), is_builtin=False,
        )
        # invalidate the module-level preset cache so the next compile
        # and any still-open PresetPanel pick up the saved changes without
        # having to be re-instantiated.
        reload_preset_library()
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
