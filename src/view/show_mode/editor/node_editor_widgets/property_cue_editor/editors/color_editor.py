"""Multi-segment colour property editor.

Mirrors the multi-wheel gobo editor: :meth:`set_fixtures` inspects the
currently-relevant fixtures and rebuilds one picker per colour segment.
Fixtures without colour metadata (or with a single colour engine) show
a single compact picker. The editor stores only the authored colours
in a per-segment dict -- the compiler drives the actual channel count
from the fixture lookup, so an assignment authored on one fixture does
not leak segments onto another.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import (
    QColorDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from model.color_hsi import ColorHSI
from model.ofl.capability_discovery import color_segment_count_of

from ._property_editor_base import PropertyEditorBase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from model.ofl.fixture import UsedFixture
    from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel


class _SegmentBlock:
    """Qt widgets + persistent state for a single colour segment."""

    __slots__ = ("color", "group", "pick_button", "preview")

    def __init__(
        self,
        group: QGroupBox | None,
        preview: QLabel,
        pick_button: QPushButton,
    ) -> None:
        self.group = group
        self.preview = preview
        self.pick_button = pick_button
        self.color: ColorHSI = ColorHSI(0.0, 0.0, 0.0)

    def apply_color(self, color: ColorHSI) -> None:
        self.color = color.copy()
        r, g, b = self.color.to_rgb()
        self.preview.setStyleSheet(f"background-color: rgb({r}, {g}, {b});")


class ColorEditor(PropertyEditorBase):
    """Edit one HSI colour per fixture segment (compact single picker when N=1)."""

    def __init__(self, model: PropertyCueFilterModel, parent: QWidget | None = None) -> None:
        super().__init__(model, "color", parent)
        self._fixtures: list[UsedFixture] = []

    def _install_manual_widgets(self, layout: QVBoxLayout) -> None:
        # Horizontal row of segment group-boxes so N>1 stays scannable.
        self._segment_layout = QHBoxLayout()
        layout.addLayout(self._segment_layout)
        self._segment_blocks: list[_SegmentBlock] = []
        self._rebuild_segments(1)

    def _clear_segments(self) -> None:
        while self._segment_layout.count() > 0:
            item = self._segment_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._segment_blocks.clear()

    def _rebuild_segments(self, count: int) -> None:
        self._clear_segments()
        n = max(1, int(count))
        for i in range(n):
            if n == 1:
                container = QWidget()
                row = QHBoxLayout()
                container.setLayout(row)
                preview = QLabel("")
                preview.setMinimumWidth(60)
                preview.setAutoFillBackground(True)
                pick = QPushButton("Pick colour...")
                row.addWidget(preview)
                row.addWidget(pick)
                self._segment_layout.addWidget(container)
                block = _SegmentBlock(None, preview, pick)
            else:
                group = QGroupBox(f"Segment {i}")
                col = QVBoxLayout()
                group.setLayout(col)
                preview = QLabel("")
                preview.setMinimumWidth(60)
                preview.setMinimumHeight(24)
                preview.setAutoFillBackground(True)
                pick = QPushButton("Pick...")
                col.addWidget(preview)
                col.addWidget(pick)
                self._segment_layout.addWidget(group)
                block = _SegmentBlock(group, preview, pick)
            pick.clicked.connect(lambda _checked=False, b=block: self._on_pick(b))
            block.apply_color(ColorHSI(0.0, 0.0, 0.0))
            self._segment_blocks.append(block)
        self._segment_layout.addStretch(1)

    def set_fixtures(self, fixtures: Iterable[UsedFixture]) -> None:
        """Rebuild one block per segment of the highest-segment colour fixture.

        Fixtures without colour segments fall back to 1 segment so single-
        colour fixtures keep the single-picker UI.
        """
        self._fixtures = list(fixtures)
        counts = [color_segment_count_of(f) for f in self._fixtures] if self._fixtures else []
        count = max([c for c in counts if c > 0], default=1)
        if count != len(self._segment_blocks):
            # Preserve previously-authored colours by index.
            preserved = [b.color.copy() for b in self._segment_blocks]
            self._rebuild_segments(count)
            for i, block in enumerate(self._segment_blocks):
                if i < len(preserved):
                    block.apply_color(preserved[i])

    def _on_pick(self, block: _SegmentBlock) -> None:
        picked = QColorDialog.getColor(block.color.to_qt_color(), self, "Pick colour")
        if not picked.isValid():
            return
        block.apply_color(ColorHSI.from_qt_color(picked))

    def _manual_values(self) -> dict[str, Any]:
        return {"colors": {i: block.color.copy() for i, block in enumerate(self._segment_blocks)}}

    def _load_manual_values(self, values: dict[str, Any]) -> None:
        raw = values.get("colors", {}) or {}
        colors: dict[int, ColorHSI] = {}
        for raw_key, raw_val in raw.items():
            try:
                index = int(raw_key)
            except (TypeError, ValueError):
                continue
            if isinstance(raw_val, ColorHSI):
                colors[index] = raw_val
        for i, block in enumerate(self._segment_blocks):
            block.apply_color(colors.get(i, ColorHSI(0.0, 0.0, 0.0)))
