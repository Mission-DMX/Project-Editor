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
    QSizePolicy,
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
        """Initialize the colour editor bound to the given cue filter model."""
        super().__init__(model, "color", parent)
        self._fixtures: list[UsedFixture] = []
        # Reuse a single QColorDialog across pick clicks. Constructing a new
        # dialog each time hits the native colour-picker portal on Linux (XDG
        # portal IPC can stall several hundred ms) and also re-allocates Qt's
        # own fallback widgets, both of which add visible latency. Forcing
        # ``DontUseNativeDialog`` keeps every picker inside Qt's own code path.
        self._color_dialog: QColorDialog | None = None

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
                # Cap the preview so a large dialog height doesn't let the
                # colour swatch stretch to fill the whole pane.
                preview.setMaximumHeight(64)
                preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
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
                preview.setMaximumHeight(64)
                preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                preview.setAutoFillBackground(True)
                pick = QPushButton("Pick...")
                col.addWidget(preview)
                col.addWidget(pick)
                # Copy this segment's colour to every other segment in the
                # same fixture. Useful when the user wants a single uniform
                # hue across all segments without clicking through the
                # picker N times.
                apply_all = QPushButton("Apply to all others")
                col.addWidget(apply_all)
                self._segment_layout.addWidget(group)
                block = _SegmentBlock(group, preview, pick)
                apply_all.clicked.connect(
                    lambda _checked=False, b=block: self._on_apply_to_all_others(b),
                )
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
        dialog = self._ensure_color_dialog()
        dialog.setCurrentColor(block.color.to_qt_color())
        if dialog.exec() != QColorDialog.DialogCode.Accepted:
            return
        picked = dialog.selectedColor()
        if not picked.isValid():
            return
        block.apply_color(ColorHSI.from_qt_color(picked))

    def _ensure_color_dialog(self) -> QColorDialog:
        """Lazily build a reusable, non-native colour dialog.

        The native XDG colour-picker portal on Linux stalls on IPC round trips
        and the native fallback allocates heavy widget trees on every open;
        reusing one Qt-native dialog drops the picker latency to one frame.
        """
        if self._color_dialog is None:
            dialog = QColorDialog(self)
            dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, on=True)
            dialog.setWindowTitle("Pick colour")
            self._color_dialog = dialog
        return self._color_dialog

    def _on_apply_to_all_others(self, source: _SegmentBlock) -> None:
        """Copy ``source``'s current colour to every other segment of this fixture."""
        for block in self._segment_blocks:
            if block is source:
                continue
            block.apply_color(source.color)

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
