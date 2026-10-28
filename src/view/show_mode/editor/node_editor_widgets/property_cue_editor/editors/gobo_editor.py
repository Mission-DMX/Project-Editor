"""Multi-wheel gobo property editor with per-wheel slot previews.

:meth:`set_fixtures` inspects the first fixture that carries gobo wheels and
builds one labelled sub-block per wheel (slot combo + rotation spinbox). When
no fixtures expose gobo metadata, a single generic ``Slot 0..15`` sub-block is
shown so authoring still works. Slot previews use the shared
:meth:`model.ofl.ofl_fixture.WheelSlot.pixmap` helper so the base64 decoding
stays in the model layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
    QWidget,
)

from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard._capability_discovery import (
    gobo_wheels_of,
)
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from model.ofl.fixture import UsedFixture
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


_FALLBACK_SLOTS = tuple((f"Slot {i}", i) for i in range(16))
_PREVIEW_SIZE = QSize(32, 32)


class _WheelBlock:
    """Qt widgets + persistent state for a single gobo wheel row."""

    __slots__ = ("group", "rotation", "slot_combo")

    def __init__(self, group: QGroupBox, slot_combo: QComboBox, rotation: JogwheelDoubleSpinBox) -> None:
        self.group = group
        self.slot_combo = slot_combo
        self.rotation = rotation


class GoboEditor(PropertyEditorBase):
    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "gobo", parent)
        self._fixtures: list[UsedFixture] = []

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        self._wheel_layout = QVBoxLayout()
        layout.addLayout(self._wheel_layout)
        self._wheel_blocks: list[_WheelBlock] = []
        self._rebuild_wheels(wheel_defs=[("Wheel 1", None)])

    def _clear_wheels(self) -> None:
        while self._wheel_layout.count() > 0:
            item = self._wheel_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._wheel_blocks.clear()

    def _rebuild_wheels(self, wheel_defs: list[tuple[str, Any]]) -> None:
        """``wheel_defs`` is a list of ``(label, wheel_or_None)`` tuples."""
        self._clear_wheels()
        for label, wheel in wheel_defs:
            group = QGroupBox(label)
            form = QFormLayout()
            group.setLayout(form)
            slot_combo = QComboBox()
            slot_combo.setIconSize(_PREVIEW_SIZE)
            if wheel is None:
                for slot_label, val in _FALLBACK_SLOTS:
                    slot_combo.addItem(slot_label, val)
            else:
                for index, slot in enumerate(getattr(wheel, "slots", [])):
                    slot_label = f"{index}: {slot.name or slot.type.value or 'slot'}"
                    pix = slot.pixmap()
                    if pix is not None:
                        slot_combo.addItem(QIcon(pix), slot_label, index)
                    else:
                        slot_combo.addItem(slot_label, index)
            rotation = JogwheelDoubleSpinBox()
            rotation.setRange(-100.0, 100.0)
            rotation.setDecimals(4)
            form.addRow("Slot", slot_combo)
            form.addRow("Rotation", rotation)
            self._wheel_layout.addWidget(group)
            self._wheel_blocks.append(_WheelBlock(group, slot_combo, rotation))

    def set_fixtures(self, fixtures: Iterable[UsedFixture]) -> None:
        """Rebuild one sub-block per gobo wheel of the first gobo-equipped fixture.

        Fixtures with multiple gobo wheels (e.g. the Varytec Hero Spot 230 has
        a "Gobo Wheel" and a "Rotatable Gobo Wheel") produce one sub-block each.
        Mixed-fixture groups fall back to the first fixture that carries gobo
        wheels; others keep the generic 0-15 slot fallback.
        """
        self._fixtures = list(fixtures)
        wheels = next(
            (gobo_wheels_of(fixture) for fixture in self._fixtures if gobo_wheels_of(fixture)),
            [],
        )
        if not wheels:
            self._rebuild_wheels(wheel_defs=[("Wheel 1", None)])
            return
        self._rebuild_wheels(wheel_defs=[(name, wheel) for name, wheel in wheels])

    def _manual_values(self) -> dict[str, Any]:
        slots: dict[int, int] = {}
        rotations: dict[int, float] = {}
        for i, block in enumerate(self._wheel_blocks):
            slots[i] = int(block.slot_combo.currentData())
            rotations[i] = float(block.rotation.value())
        return {
            "wheel_count": len(self._wheel_blocks),
            "slots": slots,
            "rotations": rotations,
        }

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        slots = values.get("slots", {})
        rotations = values.get("rotations", {})
        for i, block in enumerate(self._wheel_blocks):
            want = int(slots.get(i, 0)) if isinstance(slots, dict) else 0
            for idx in range(block.slot_combo.count()):
                if block.slot_combo.itemData(idx) == want:
                    block.slot_combo.setCurrentIndex(idx)
                    break
            rot = float(rotations.get(i, 0.0)) if isinstance(rotations, dict) else 0.0
            block.rotation.setValue(rot)
