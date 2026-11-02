"""Right-hand editor panel: fixture list, property form and DMX device mapping."""

from __future__ import annotations

import math
import time
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from model.visualizer.dmx.dmx_parser import ColorRole, MovementRole, auto_detect_mapping, parse_pan_tilt_range
from model.visualizer.stage.so_moving_head import MovingHead
from model.visualizer.stage.so_par_can import ParCan
from model.visualizer.stage.so_pixel_fixture import PixelFixture
from view.visualizer.add_fixture_dialog import AddFixtureDialog, fixture_label
from view.visualizer.stage_group_name_dialog import GroupNameDialog

if TYPE_CHECKING:
    from model.ofl.fixture import UsedFixture
    from model.visualizer.stage.fixture_group import FixtureGroup
    from model.visualizer.stage.stage_config import StageConfig
    from model.visualizer.stage.stage_object import StageObject

logger = getLogger(__name__)


def _fixture_combo_data(fix: UsedFixture) -> dict[str, int | list[str]]:
    """Extract the data dict needed for device combo boxes from a UsedFixture."""
    ch_names = [ch.name for ch in fix.fixture_channels]
    return {
        "universe": fix.universe_id,
        "start_channel": fix.start_index,
        "channel_count": fix.channel_length,
        "channel_names": ch_names,
    }


ROLE_ID = QtCore.Qt.ItemDataRole.UserRole
ROLE_IS_GROUP = QtCore.Qt.ItemDataRole.UserRole + 1  # bool: True for group headers


class StageEditorWidget(QtWidgets.QWidget):
    """Right-hand panel: fixture list + property editor + DMX controls."""

    add_object_requested = QtCore.Signal(str, str, object)  # (fixture_key, name, device_or_None)
    remove_object_requested = QtCore.Signal(str)  # object_id
    object_changed = QtCore.Signal(str)  # object_id
    selection_changed = QtCore.Signal(list, bool)  # (highlight_ids, is_multi)
    group_requested = QtCore.Signal(list, str)  # (fixture_ids, group_name)
    remove_group_requested = QtCore.Signal(str)  # group_id
    dmx_toggled = QtCore.Signal(bool)  # True = start, False = stop

    def __init__(
        self,
        stage_config: StageConfig,
        used_fixtures: list[UsedFixture] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initialize Stage Editor Widget.

        Args:
            stage_config: The stage configuration to provide an editor for.
            used_fixtures: The fixtures a user may select from when adding to the stage
            parent: The parent widget.

        """
        super().__init__(parent)
        self._stage_config = stage_config
        self._used_fixtures = used_fixtures or []
        self._current_obj: StageObject | None = None  # currently selected fixture
        self._current_group: FixtureGroup | None = None  # currently selected group
        self._updating_ui = False  # guard against recursive signal loops
        self._group_base_offsets: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]] = {}
        self._group_base_rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._last_live_update = 0.0  # throttle for DMX live refresh

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(6)

        # Fixture list header with action buttons
        list_header = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("Fixtures")
        fnt = lbl.font()
        fnt.setBold(True)
        fnt.setPointSize(fnt.pointSize() + 1)
        lbl.setFont(fnt)
        list_header.addWidget(lbl)
        list_header.addStretch(1)

        self._add_btn = QtWidgets.QPushButton("Add")
        self._remove_btn = QtWidgets.QPushButton("Remove")
        self._group_btn = QtWidgets.QPushButton("Group")
        self._add_btn.setFixedWidth(60)
        self._remove_btn.setFixedWidth(60)
        self._group_btn.setFixedWidth(60)
        self._group_btn.setToolTip("Group selected fixtures (Shift/Ctrl to multi-select)")
        list_header.addWidget(self._add_btn)
        list_header.addWidget(self._remove_btn)
        list_header.addWidget(self._group_btn)

        # DMX live toggle checkbox
        self._dmx_cb = QtWidgets.QCheckBox("DMX Live")
        self._dmx_cb.setChecked(True)
        self._dmx_cb.setToolTip("Enable/disable live DMX reception from Fish")
        self._dmx_cb.toggled.connect(self._on_dmx_live_toggled)
        list_header.addWidget(self._dmx_cb)

        root.addLayout(list_header)

        # Fixture list widget
        self._fixture_list = QtWidgets.QListWidget()
        self._fixture_list.setMaximumHeight(200)
        self._fixture_list.setAlternatingRowColors(True)
        self._fixture_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        root.addWidget(self._fixture_list)

        # Scrollable property panel
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._prop_container = QtWidgets.QWidget()
        self._prop_layout = QtWidgets.QFormLayout(self._prop_container)
        self._prop_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self._prop_layout.setContentsMargins(0, 0, 0, 0)
        self._prop_layout.setVerticalSpacing(5)
        scroll.setWidget(self._prop_container)
        root.addWidget(scroll, 1)

        # Connect button signals
        self._add_btn.clicked.connect(self._on_add_clicked)
        self._remove_btn.clicked.connect(self._on_remove_clicked)
        self._group_btn.clicked.connect(self._on_group_clicked)
        self._fixture_list.itemSelectionChanged.connect(self._on_selection_changed)

        # Build initial list
        self._rebuild_list()

    # Fixture list building

    def _display_text(self, obj: StageObject) -> str:
        """Format display text for a fixture list item."""
        display = obj.get_display_name()
        if obj.name:
            return f"{obj.name}  ({display})"
        return display

    def _group_display_text(self, grp: FixtureGroup) -> str:
        """Format display text for a group header list item."""
        count = len(grp.member_ids)
        name = grp.name or grp.id
        return f"[G] {name}  ({count} fixtures)"

    def _rebuild_list(self) -> None:
        """Full rebuild of the fixture list (after group creation/removal etc.)."""
        self._fixture_list.blockSignals(True)
        self._fixture_list.clear()

        # Collect fixture IDs that belong to any group
        grouped_ids = set()
        for grp in self._stage_config.groups:
            grouped_ids.update(grp.member_ids)

        # Add groups with their member fixtures indented below
        for grp in self._stage_config.groups:
            # Group header item (bold, colored background)
            grp_item = QtWidgets.QListWidgetItem(self._group_display_text(grp))
            grp_item.setData(ROLE_ID, grp.id)
            grp_item.setData(ROLE_IS_GROUP, True)
            grp_item.setBackground(QtGui.QColor(50, 55, 75))
            grp_item.setForeground(QtGui.QColor(190, 195, 255))
            fnt = grp_item.font()
            fnt.setBold(True)
            grp_item.setFont(fnt)
            self._fixture_list.addItem(grp_item)

            # Member fixtures indented with tree connector
            for mid in grp.member_ids:
                obj = self._stage_config.get_object(mid)
                if obj is None:
                    continue
                text = f"    \u2514 {self._display_text(obj)}"
                item = QtWidgets.QListWidgetItem(text)
                item.setData(ROLE_ID, obj.id)
                item.setData(ROLE_IS_GROUP, False)
                self._fixture_list.addItem(item)

        # Add ungrouped fixtures
        for obj in self._stage_config.objects:
            if obj.get_type() == "platform":
                continue
            if obj.id in grouped_ids:
                continue  # already shown under its group
            item = QtWidgets.QListWidgetItem(self._display_text(obj))
            item.setData(ROLE_ID, obj.id)
            item.setData(ROLE_IS_GROUP, False)
            self._fixture_list.addItem(item)

        self._fixture_list.blockSignals(False)

        # Auto-select first item
        if self._fixture_list.count() > 0:
            self._fixture_list.setCurrentRow(0)
        else:
            self._clear_properties()

    # Selection handling

    def _on_selection_changed(self) -> None:
        """React to list selection changes and update the property panel."""
        selected_items = self._fixture_list.selectedItems()
        if not selected_items:
            self._current_obj = None
            self._current_group = None
            self._clear_properties()
            self.selection_changed.emit([], False)
            return

        # Collect all fixture IDs that should be highlighted in 3D
        highlight_ids = []
        for item in selected_items:
            oid = item.data(ROLE_ID)
            is_group = item.data(ROLE_IS_GROUP)
            if is_group:
                grp = self._stage_config.get_group(oid)
                if grp:
                    highlight_ids.extend(grp.member_ids)
            else:
                highlight_ids.append(oid)

        is_multi = len(highlight_ids) > 1

        # Build properties for the last clicked item
        last_item = selected_items[-1]
        last_id = last_item.data(ROLE_ID)
        is_group = last_item.data(ROLE_IS_GROUP)

        if is_group:
            grp = self._stage_config.get_group(last_id)
            if grp:
                self._current_obj = None
                self._current_group = grp
                self._build_group_properties(grp)
        else:
            obj = self._stage_config.get_object(last_id)
            if obj:
                self._current_obj = obj
                self._current_group = None
                self._build_properties(obj)

        # Enable group button only if 2+ non-group fixtures are selected
        fixture_count = sum(1 for it in selected_items if not it.data(ROLE_IS_GROUP))
        self._group_btn.setEnabled(fixture_count >= 2)

        self.selection_changed.emit(highlight_ids, is_multi)

    # Property panel helpers

    def _clear_properties(self) -> None:
        """Remove all rows from the property form."""
        while self._prop_layout.rowCount() > 0:
            self._prop_layout.removeRow(0)

    def _add_section_header(self, text: str) -> None:
        """Add a bold section header label to the property form."""
        lbl = QtWidgets.QLabel(text)
        fnt = lbl.font()
        fnt.setBold(True)
        lbl.setFont(fnt)
        self._prop_layout.addRow(lbl)

    def _add_separator(self) -> None:
        """Add a horizontal line separator to the property form."""
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self._prop_layout.addRow(line)

    # Group property panel

    def _build_group_properties(self, grp: FixtureGroup) -> None:
        """Build the property panel for a selected fixture group."""
        self._updating_ui = True
        self._clear_properties()

        # Snapshot: store each member's offset from group center + rotation
        cx, cy, cz = grp.position
        self._group_base_offsets = {}
        for mid in grp.member_ids:
            obj = self._stage_config.get_object(mid)
            if obj:
                offset = (obj.position[0] - cx, obj.position[1] - cy, obj.position[2] - cz)
                self._group_base_offsets[mid] = (offset, obj.rotation)
        self._group_base_rotation = grp.rotation

        self._add_section_header("[G] Group")

        self._name_edit = QtWidgets.QLineEdit(grp.name)
        self._name_edit.setPlaceholderText("Group")
        self._name_edit.textChanged.connect(self._on_group_name_changed)
        self._prop_layout.addRow("Name:", self._name_edit)

        self._add_separator()
        self._add_section_header("Group Position (moves all members)")

        self._pos_spins = []
        for i, axis in enumerate(("X:", "Y:", "Z:")):
            sp = QtWidgets.QDoubleSpinBox()
            sp.setRange(-5000, 5000)
            sp.setDecimals(1)
            sp.setSingleStep(1.0)
            sp.setSuffix("  u")
            sp.setValue(grp.position[i])
            sp.valueChanged.connect(self._on_group_position_changed)
            self._prop_layout.addRow(axis, sp)
            self._pos_spins.append(sp)

        self._add_separator()
        self._add_section_header("Group Rotation (rotates all members)")

        self._rot_spins = []
        for i, axis in enumerate(("X:", "Y:", "Z:")):
            sp = QtWidgets.QDoubleSpinBox()
            sp.setRange(-360, 360)
            sp.setDecimals(1)
            sp.setSingleStep(5.0)
            sp.setSuffix("  deg")
            sp.setValue(grp.rotation[i])
            sp.valueChanged.connect(self._on_group_rotation_changed)
            self._prop_layout.addRow(axis, sp)
            self._rot_spins.append(sp)

        self._add_separator()
        self._add_section_header(f"Members ({len(grp.member_ids)})")
        for mid in grp.member_ids:
            obj = self._stage_config.get_object(mid)
            name_str = self._display_text(obj) if obj else mid
            lbl = QtWidgets.QLabel(name_str)
            self._prop_layout.addRow("", lbl)

        self._updating_ui = False

    # Fixture property panel

    def _build_properties(self, obj: StageObject) -> None:
        """Build the property panel for a single selected fixture."""
        self._updating_ui = True
        self._clear_properties()

        # Name
        self._name_edit = QtWidgets.QLineEdit(obj.name)
        self._name_edit.setPlaceholderText(obj.get_display_name())
        self._name_edit.textChanged.connect(self._on_name_changed)
        self._prop_layout.addRow("Name:", self._name_edit)

        # Device Link (DMX)
        if isinstance(obj, MovingHead):
            self._add_separator()
            self._build_device_section(obj)
        elif isinstance(obj, ParCan):
            self._add_separator()
            self._build_parcan_device_section(obj)
        elif isinstance(obj, PixelFixture):
            self._add_separator()
            self._build_pixel_device_section(obj)

        # Position
        self._add_separator()
        self._add_section_header("Position")

        self._pos_spins = []
        for i, axis in enumerate(("X:", "Y:", "Z:")):
            sp = QtWidgets.QDoubleSpinBox()
            sp.setRange(-5000, 5000)
            sp.setDecimals(1)
            sp.setSingleStep(1.0)
            sp.setSuffix("  u")
            sp.setValue(obj.position[i])
            sp.valueChanged.connect(self._on_position_changed)
            self._prop_layout.addRow(axis, sp)
            self._pos_spins.append(sp)

        # Rotation
        self._add_separator()
        self._add_section_header("Rotation")

        self._rot_spins = []
        for i, axis in enumerate(("X:", "Y:", "Z:")):
            sp = QtWidgets.QDoubleSpinBox()
            sp.setRange(-360, 360)
            sp.setDecimals(1)
            sp.setSingleStep(5.0)
            sp.setSuffix("  deg")
            sp.setValue(obj.rotation[i])
            sp.valueChanged.connect(self._on_rotation_changed)
            self._prop_layout.addRow(axis, sp)
            self._rot_spins.append(sp)

        # Scale
        self._add_separator()

        self._scale_spin = QtWidgets.QDoubleSpinBox()
        self._scale_spin.setRange(0.01, 1000)
        self._scale_spin.setDecimals(2)
        self._scale_spin.setSingleStep(0.5)
        self._scale_spin.setValue(obj.scale)
        self._scale_spin.valueChanged.connect(self._on_scale_changed)
        self._prop_layout.addRow("Scale:", self._scale_spin)

        # MovingHead beam properties
        if isinstance(obj, MovingHead):
            self._setup_movinghead_settings(obj)

        # PAR can beam properties (same shape as moving head, minus pan/tilt)
        if isinstance(obj, ParCan):
            self._setup_parcan_settings(obj)

        # Pixel fixture layout properties (LED bar, matrix blinder)
        if isinstance(obj, PixelFixture):
            self._setup_pixel_fixture_settings(obj)

        self._updating_ui = False

    def _setup_pixel_fixture_settings(self, obj: PixelFixture) -> None:
        """Add matrix + physical-dimension editors for pixel fixtures."""
        self._add_separator()
        self._add_section_header("Pixel Matrix")

        cols, rows = obj.pixel_matrix
        self._pixel_cols_spin = QtWidgets.QSpinBox()
        self._pixel_cols_spin.setRange(1, 512)
        self._pixel_cols_spin.setValue(cols)
        self._pixel_cols_spin.valueChanged.connect(self._on_pixel_matrix_changed)
        self._prop_layout.addRow("Cols:", self._pixel_cols_spin)

        self._pixel_rows_spin = QtWidgets.QSpinBox()
        self._pixel_rows_spin.setRange(1, 512)
        self._pixel_rows_spin.setValue(rows)
        self._pixel_rows_spin.valueChanged.connect(self._on_pixel_matrix_changed)
        self._prop_layout.addRow("Rows:", self._pixel_rows_spin)

        self._add_separator()
        self._add_section_header("Physical Dimensions")

        w, h, d = obj.physical_size
        self._physical_spins: list[QtWidgets.QDoubleSpinBox] = []
        for axis, val in (("Width:", w), ("Height:", h), ("Depth:", d)):
            sp = QtWidgets.QDoubleSpinBox()
            sp.setRange(1.0, 20000.0)
            sp.setDecimals(1)
            sp.setSingleStep(10.0)
            sp.setSuffix("  mm")
            sp.setValue(val)
            sp.valueChanged.connect(self._on_physical_size_changed)
            self._prop_layout.addRow(axis, sp)
            self._physical_spins.append(sp)

    def _on_pixel_matrix_changed(self) -> None:
        if self._updating_ui or not isinstance(self._current_obj, PixelFixture):
            return
        cols = self._pixel_cols_spin.value()
        rows = self._pixel_rows_spin.value()
        self._current_obj.pixel_matrix = (cols, rows)
        self._emit_changed()

    def _on_physical_size_changed(self) -> None:
        if self._updating_ui or not isinstance(self._current_obj, PixelFixture):
            return
        w = self._physical_spins[0].value()
        h = self._physical_spins[1].value()
        d = self._physical_spins[2].value()
        self._current_obj.physical_size = (w, h, d)
        self._emit_changed()

    def _build_pixel_device_section(self, obj: PixelFixture) -> None:
        """Show and edit the DMX device that drives a pixel fixture.

        Displays the current base address (universe + start channel) and the
        detected master dimmer offset, and lets the user reassign the linked
        device via the same combo used for moving heads.
        """
        self._add_section_header("DMX Device")

        self._pix_device_combo = QtWidgets.QComboBox(self._prop_container)
        self._pix_device_combo.addItem("(None)", None)
        for fix in self._used_fixtures:
            self._pix_device_combo.addItem(fixture_label(fix), fix)

        pixel_cfg = (obj.device_config or {}).get("pixels") or {}
        current_universe = pixel_cfg.get("universe")
        current_start = pixel_cfg.get("start_channel")
        self._pix_device_combo.setCurrentIndex(0)
        if current_universe is not None and current_start is not None:
            for i in range(1, self._pix_device_combo.count()):
                fix = self._pix_device_combo.itemData(i)
                if fix is not None and fix.universe_id == current_universe and fix.start_index == current_start:
                    self._pix_device_combo.setCurrentIndex(i)
                    break
        self._pix_device_combo.currentIndexChanged.connect(self._on_pixel_device_changed)
        self._prop_layout.addRow("Device:", self._pix_device_combo)

        self._pix_address_label = QtWidgets.QLabel()
        self._prop_layout.addRow("Address:", self._pix_address_label)

        self._pix_dimmer_label = QtWidgets.QLabel()
        self._prop_layout.addRow("Dimmer CH:", self._pix_dimmer_label)

        self._pix_pixel_count_label = QtWidgets.QLabel()
        self._prop_layout.addRow("Mapped px:", self._pix_pixel_count_label)

        self._refresh_pixel_device_labels(obj)

    def _refresh_pixel_device_labels(self, obj: PixelFixture) -> None:
        """Update the read-only DMX info labels from the fixture's current mapping."""
        pixel_cfg = (obj.device_config or {}).get("pixels") or {}
        universe = pixel_cfg.get("universe")
        start = pixel_cfg.get("start_channel")
        count = pixel_cfg.get("channel_count")
        dimmer = pixel_cfg.get("dimmer", -1)
        entries = pixel_cfg.get("channels") or []

        if universe is not None and start is not None:
            # Users think in 1-based DMX addresses, so show that alongside the internal offset.
            addr_text = f"Universe {universe}, CH{start + 1}"
            if count:
                addr_text += f"  ({count} ch)"
        else:
            addr_text = "(not linked)"
        self._pix_address_label.setText(addr_text)

        if isinstance(dimmer, int) and dimmer >= 0:
            if universe is not None and start is not None:
                self._pix_dimmer_label.setText(f"CH{dimmer + 1} (offset {dimmer - start})")
            else:
                self._pix_dimmer_label.setText(f"CH{dimmer + 1}")
        else:
            self._pix_dimmer_label.setText("(none)")

        mapped = sum(1 for e in entries if isinstance(e, dict) and any(e.get(k, -1) >= 0 for k in ("r", "g", "b", "w")))
        self._pix_pixel_count_label.setText(f"{mapped} / {len(entries)}")

    def _on_pixel_device_changed(self, _: int) -> None:
        if self._updating_ui or not isinstance(self._current_obj, PixelFixture):
            return
        selected = self._pix_device_combo.currentData()
        if selected is None:
            if self._current_obj.device_config:
                self._current_obj.device_config.pop("pixels", None)
                if not self._current_obj.device_config:
                    self._current_obj.device_config = None
        else:
            # Delegate to the visualizer widget's auto-configure so the same
            # channel-name parsing runs here as in the add-fixture flow.
            parent = self.parent()
            configure = getattr(parent, "_auto_configure_pixel_fixture", None)
            if callable(configure):
                configure(self._current_obj, selected)
            else:
                logger.warning("Cannot auto-configure pixel fixture: parent has no _auto_configure_pixel_fixture")

        # Auto-configure may have adjusted matrix/dimensions from the new fixture
        # definition; push the new values into the matching spin boxes without
        # re-triggering their change handlers.
        self._updating_ui = True
        try:
            if hasattr(self, "_pixel_cols_spin") and hasattr(self, "_pixel_rows_spin"):
                cols, rows = self._current_obj.pixel_matrix
                self._pixel_cols_spin.setValue(cols)
                self._pixel_rows_spin.setValue(rows)
            if hasattr(self, "_physical_spins") and len(self._physical_spins) == 3:
                w, h, d = self._current_obj.physical_size
                self._physical_spins[0].setValue(w)
                self._physical_spins[1].setValue(h)
                self._physical_spins[2].setValue(d)
        finally:
            self._updating_ui = False

        self._refresh_pixel_device_labels(self._current_obj)
        self._emit_changed()

    def _build_parcan_device_section(self, obj: ParCan) -> None:
        """Show and edit the DMX device that drives a PAR can.

        PAR cans have no pan/tilt: only the dimmer and RGB(W) channels are shown.
        A single device selector configures both since a PAR can's dimmer and
        colour channels come from the same OFL fixture in practice.
        """
        self._add_section_header("DMX Device")

        self._par_device_combo = QtWidgets.QComboBox(self._prop_container)
        self._par_device_combo.addItem("(None)", None)
        for fix in self._used_fixtures:
            self._par_device_combo.addItem(fixture_label(fix), fix)

        dc = obj.device_config or {}
        # Look for the currently-linked device in either section — they should be
        # the same fixture, but we pick whichever is set to seed the combo.
        current_universe = None
        current_start = None
        for section in ("color", "movement"):
            sub = dc.get(section) or {}
            if "universe" in sub and "start_channel" in sub:
                current_universe = sub["universe"]
                current_start = sub["start_channel"]
                break

        self._par_device_combo.setCurrentIndex(0)
        if current_universe is not None and current_start is not None:
            for i in range(1, self._par_device_combo.count()):
                fix = self._par_device_combo.itemData(i)
                if fix is not None and fix.universe_id == current_universe and fix.start_index == current_start:
                    self._par_device_combo.setCurrentIndex(i)
                    break
        self._par_device_combo.currentIndexChanged.connect(self._on_par_device_changed)
        self._prop_layout.addRow("Device:", self._par_device_combo)

        self._par_address_label = QtWidgets.QLabel()
        self._prop_layout.addRow("Address:", self._par_address_label)

        self._par_dimmer_label = QtWidgets.QLabel()
        self._prop_layout.addRow("Dimmer CH:", self._par_dimmer_label)

        self._par_color_label = QtWidgets.QLabel()
        self._prop_layout.addRow("Colour CH:", self._par_color_label)

        self._refresh_parcan_device_labels(obj)

    def _refresh_parcan_device_labels(self, obj: ParCan) -> None:
        """Update the DMX info labels for a PAR can from its current mapping."""
        dc = obj.device_config or {}
        mv = dc.get("movement") or {}
        col = dc.get("color") or {}

        universe = mv.get("universe") if mv else col.get("universe")
        start = mv.get("start_channel") if mv else col.get("start_channel")
        count = mv.get("channel_count") if mv else col.get("channel_count")

        if universe is not None and start is not None:
            addr = f"Universe {universe}, CH{start + 1}"
            if count:
                addr += f"  ({count} ch)"
        else:
            addr = "(not linked)"
        self._par_address_label.setText(addr)

        mv_map = mv.get("mapping", {}) if mv else {}
        dim_off = int(mv_map.get(MovementRole.DIMMER.value, -1))
        mv_start = mv.get("start_channel", 0) if mv else 0
        if dim_off >= 0:
            self._par_dimmer_label.setText(f"CH{mv_start + dim_off + 1} (offset {dim_off})")
        else:
            self._par_dimmer_label.setText("(none)")

        col_map = col.get("mapping", {}) if col else {}
        col_start = col.get("start_channel", 0) if col else 0
        role_bits = []
        for role in ("red", "green", "blue", "white"):
            off = int(col_map.get(role, -1))
            if off >= 0:
                role_bits.append(f"{role[0].upper()}=CH{col_start + off + 1}")
        self._par_color_label.setText(", ".join(role_bits) if role_bits else "(none)")

    def _on_par_device_changed(self, _: int) -> None:
        if self._updating_ui or not isinstance(self._current_obj, ParCan):
            return
        selected = self._par_device_combo.currentData()
        if selected is None:
            self._current_obj.device_config = None
        else:
            parent = self.parent()
            configure = getattr(parent, "_auto_configure_par_can", None)
            if callable(configure):
                configure(self._current_obj, selected)
            else:
                logger.warning("Cannot auto-configure PAR can: parent has no _auto_configure_par_can")
        self._refresh_parcan_device_labels(self._current_obj)
        self._apply_dmx_locks(self._current_obj)
        self._emit_changed()

    def _setup_parcan_settings(self, obj: ParCan) -> None:
        """Beam / dimmer / colour controls for a PAR can.

        Mirrors the moving-head editor UI (same widget names so :meth:`_apply_dmx_locks`
        and :meth:`update_live_values` can drive both), but without the pan/tilt row.
        """
        self._add_separator()
        self._add_section_header("Beam Control")

        self._beam_cb = QtWidgets.QCheckBox("Enabled")
        self._beam_cb.setChecked(obj.beam_on)
        self._beam_cb.stateChanged.connect(self._on_beam_toggled)
        self._prop_layout.addRow("Beam:", self._beam_cb)

        self._dimmer_spin = QtWidgets.QDoubleSpinBox()
        self._dimmer_spin.setRange(0, 1)
        self._dimmer_spin.setDecimals(2)
        self._dimmer_spin.setSingleStep(0.05)
        self._dimmer_spin.setValue(obj.dimmer)
        self._dimmer_spin.valueChanged.connect(lambda v: self._on_attr("dimmer", v))
        self._prop_layout.addRow("Dimmer:", self._dimmer_spin)

        self._dimmer_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._dimmer_slider.setRange(0, 100)
        self._dimmer_slider.setValue(int(obj.dimmer * 100))
        self._dimmer_slider.valueChanged.connect(self._on_dimmer_slider)
        self._prop_layout.addRow("", self._dimmer_slider)

        self._add_separator()
        self._add_section_header("Beam Color")

        r, g, b = obj.beam_color
        self._color_btn = QtWidgets.QPushButton()
        self._color_btn.setFixedHeight(28)
        self._update_color_btn_style(r, g, b)
        self._color_btn.clicked.connect(self._on_color_picker)
        self._prop_layout.addRow("Pick:", self._color_btn)

        self._rgb_spins = []
        for axis, val in (("R:", r), ("G:", g), ("B:", b)):
            sp = QtWidgets.QSpinBox()
            sp.setRange(0, 255)
            sp.setSingleStep(5)
            sp.setValue(val)
            sp.valueChanged.connect(self._on_rgb_changed)
            self._prop_layout.addRow(axis, sp)
            self._rgb_spins.append(sp)

        # Pan/tilt widgets don't exist for PAR cans; ``_apply_dmx_locks`` and
        # ``update_live_values`` guard on ``hasattr`` before touching them.
        self._apply_dmx_locks(obj)

    def _setup_movinghead_settings(self, obj: MovingHead) -> None:
        self._add_separator()
        self._add_section_header("Beam Control")

        pan_min, pan_max, tilt_min, tilt_max = self._get_fixture_movement_range(obj)

        self._pan_spin = QtWidgets.QDoubleSpinBox()
        self._pan_spin.setRange(pan_min, pan_max)
        self._pan_spin.setDecimals(1)
        self._pan_spin.setSingleStep(1.0)
        self._pan_spin.setSuffix("  deg")
        self._pan_spin.setValue(obj.pan)
        self._pan_spin.valueChanged.connect(lambda v: self._on_attr("pan", v))
        self._prop_layout.addRow("Pan:", self._pan_spin)

        self._tilt_spin = QtWidgets.QDoubleSpinBox()
        self._tilt_spin.setRange(tilt_min, tilt_max)
        self._tilt_spin.setDecimals(1)
        self._tilt_spin.setSingleStep(1.0)
        self._tilt_spin.setSuffix("  deg")
        self._tilt_spin.setValue(obj.tilt)
        self._tilt_spin.valueChanged.connect(lambda v: self._on_attr("tilt", v))
        self._prop_layout.addRow("Tilt:", self._tilt_spin)

        self._add_separator()

        self._beam_cb = QtWidgets.QCheckBox("Enabled")
        self._beam_cb.setChecked(obj.beam_on)
        self._beam_cb.stateChanged.connect(self._on_beam_toggled)
        self._prop_layout.addRow("Beam:", self._beam_cb)

        self._dimmer_spin = QtWidgets.QDoubleSpinBox()
        self._dimmer_spin.setRange(0, 1)
        self._dimmer_spin.setDecimals(2)
        self._dimmer_spin.setSingleStep(0.05)
        self._dimmer_spin.setValue(obj.dimmer)
        self._dimmer_spin.valueChanged.connect(lambda v: self._on_attr("dimmer", v))
        self._prop_layout.addRow("Dimmer:", self._dimmer_spin)

        self._dimmer_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._dimmer_slider.setRange(0, 100)
        self._dimmer_slider.setValue(int(obj.dimmer * 100))
        self._dimmer_slider.valueChanged.connect(self._on_dimmer_slider)
        self._prop_layout.addRow("", self._dimmer_slider)

        # Beam color
        self._add_separator()
        self._add_section_header("Beam Color")

        r, g, b = obj.beam_color
        self._color_btn = QtWidgets.QPushButton()
        self._color_btn.setFixedHeight(28)
        self._update_color_btn_style(r, g, b)
        self._color_btn.clicked.connect(self._on_color_picker)
        self._prop_layout.addRow("Pick:", self._color_btn)

        self._rgb_spins = []
        for axis, val in [("R:", r), ("G:", g), ("B:", b)]:
            sp = QtWidgets.QSpinBox()
            sp.setRange(0, 255)
            sp.setSingleStep(5)
            sp.setValue(val)
            sp.valueChanged.connect(self._on_rgb_changed)
            self._prop_layout.addRow(axis, sp)
            self._rgb_spins.append(sp)

        # Lock controls that are driven by DMX
        self._apply_dmx_locks(obj)

    # DMX lock / unlock logic

    def _has_dmx_role(self, obj: StageObject, section: str, role: MovementRole | ColorRole) -> bool:
        """Check if a MovingHead has a DMX channel assigned for a given role."""
        dc = obj.device_config
        if not dc:
            return False
        sub = dc.get(section, {})
        mapping = sub.get("mapping", {})
        return mapping.get(role.value, -1) >= 0

    def _get_fixture_movement_range(self, obj: MovingHead) -> tuple[float, float, float, float]:
        """Pan/tilt spin limits as ``(pan_min, pan_max, tilt_min, tilt_max)`` in degrees.

        Accepts both the current 4-tuple limits format and the legacy 2-tuple span format
        possibly still stored in older stage files.
        """
        mv_cfg = (obj.device_config or {}).get("movement", {})
        return parse_pan_tilt_range(mv_cfg.get("pan_tilt_range"))

    def _on_dmx_live_toggled(self, checked: bool) -> None:
        self.dmx_toggled.emit(checked)
        self._refresh_locks()

    def _apply_dmx_locks(self, obj: StageObject) -> None:
        """Disable UI controls for channels that are driven by live DMX.

        When DMX Live is off, all controls remain unlocked for manual editing.
        Works for both moving heads and PAR cans; the pan/tilt widgets are only
        touched if they exist (they don't for PAR cans).
        """
        if not isinstance(obj, (MovingHead, ParCan)):
            return

        lock_style = "background-color: #3a3a2a; color: #aa9;"
        unlock_style = ""

        # Reset all controls to unlocked state first (guarding for widgets that
        # only exist on one of the two fixture types).
        for attr in ("_pan_spin", "_tilt_spin", "_dimmer_spin"):
            widget = getattr(self, attr, None)
            if widget is None:
                continue
            widget.setEnabled(True)
            widget.setToolTip("")
            widget.setStyleSheet(unlock_style)
        if hasattr(self, "_dimmer_slider"):
            self._dimmer_slider.setEnabled(True)
        if hasattr(self, "_beam_cb"):
            self._beam_cb.setEnabled(True)
        if hasattr(self, "_color_btn"):
            self._color_btn.setEnabled(True)
            self._color_btn.setToolTip("")
        for sp in getattr(self, "_rgb_spins", ()):
            sp.setEnabled(True)
            sp.setStyleSheet(unlock_style)

        # If DMX Live is off, keep everything unlocked
        if not self._dmx_cb.isChecked():
            return

        # Lock DMX-controlled movement channels (only applies to moving heads)
        if isinstance(obj, MovingHead):
            if self._has_dmx_role(obj, "movement", MovementRole.PAN_COARSE):
                self._pan_spin.setEnabled(False)
                self._pan_spin.setToolTip("Controlled by DMX")
                self._pan_spin.setStyleSheet(lock_style)
            if self._has_dmx_role(obj, "movement", MovementRole.TILT_COARSE):
                self._tilt_spin.setEnabled(False)
                self._tilt_spin.setToolTip("Controlled by DMX")
                self._tilt_spin.setStyleSheet(lock_style)

        has_dim = self._has_dmx_role(obj, "movement", MovementRole.DIMMER) or self._has_dmx_role(
            obj, "color", ColorRole.WHITE
        )
        if has_dim and hasattr(self, "_dimmer_spin"):
            self._dimmer_spin.setEnabled(False)
            self._dimmer_slider.setEnabled(False)
            self._beam_cb.setEnabled(False)
            self._dimmer_spin.setToolTip("Controlled by DMX")
            self._dimmer_spin.setStyleSheet(lock_style)

        # Lock DMX-controlled color channels
        has_r = self._has_dmx_role(obj, "color", ColorRole.RED)
        has_g = self._has_dmx_role(obj, "color", ColorRole.GREEN)
        has_b = self._has_dmx_role(obj, "color", ColorRole.BLUE)
        if has_r and has_g and has_b and hasattr(self, "_color_btn"):
            self._color_btn.setEnabled(False)
            self._color_btn.setToolTip("Controlled by DMX")
            for sp in self._rgb_spins:
                sp.setEnabled(False)
                sp.setStyleSheet(lock_style)

    def _refresh_locks(self) -> None:
        """Re-apply lock state after a device or mapping change."""
        obj = self._current_obj
        if obj is None:
            return
        if (isinstance(obj, MovingHead) and hasattr(self, "_pan_spin")) or (
            isinstance(obj, ParCan) and hasattr(self, "_dimmer_spin")
        ):
            self._apply_dmx_locks(obj)

    def update_live_values(self) -> None:
        """Refresh the property panel with current fixture values from DMX.

        Throttled to 10 Hz to avoid excessive UI updates during fast polling.
        """
        if not self._dmx_cb.isChecked():
            return
        now = time.time()
        if now - self._last_live_update < 0.1:
            return
        self._last_live_update = now

        obj = self._current_obj
        if not obj or not isinstance(obj, (MovingHead, ParCan)):
            return

        self._updating_ui = True
        try:
            if hasattr(self, "_pan_spin"):
                self._pan_spin.setValue(obj.pan)
            if hasattr(self, "_tilt_spin"):
                self._tilt_spin.setValue(obj.tilt)
            if hasattr(self, "_dimmer_spin"):
                self._dimmer_spin.setValue(obj.dimmer)
            if hasattr(self, "_dimmer_slider"):
                self._dimmer_slider.setValue(int(obj.dimmer * 100))
            if hasattr(self, "_beam_cb"):
                self._beam_cb.setChecked(obj.beam_on)
            if hasattr(self, "_rgb_spins") and len(self._rgb_spins) == 3:
                r, g, b = obj.beam_color
                self._rgb_spins[0].setValue(r)
                self._rgb_spins[1].setValue(g)
                self._rgb_spins[2].setValue(b)
            if hasattr(self, "_color_btn"):
                r, g, b = obj.beam_color
                self._update_color_btn_style(r, g, b)
        except Exception as e:
            logger.exception("Failed to update attribute: %s", e)
        self._updating_ui = False

    def _update_color_btn_style(self, r: float, g: float, b: float) -> None:
        """Set the color button background and auto-contrast text color."""
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        tc = "#000" if lum > 128 else "#fff"
        self._color_btn.setStyleSheet(f"background-color: rgb({r},{g},{b}); color: {tc}; border: 1px solid #555;")
        self._color_btn.setText(f"({r}, {g}, {b})")

    # Device (DMX) section — Movement and Color

    def _build_device_section(self, obj: StageObject) -> None:
        """Build the Movement Device and Color Device property sections."""
        if not isinstance(obj, MovingHead):
            return

        dc = obj.device_config or {}

        # Movement Device (Pan/Tilt/Dimmer)
        self._add_section_header("Movement Device (Pan/Tilt/Dimmer)")
        self._mv_device_combo = QtWidgets.QComboBox(self._prop_container)
        self._mv_device_combo.addItem("(None)", None)
        for fix in self._used_fixtures:
            self._mv_device_combo.addItem(fixture_label(fix), _fixture_combo_data(fix))

        # Pre-select the matching device if already configured
        self._mv_device_combo.setCurrentIndex(0)
        mv_cfg = dc.get("movement")
        if mv_cfg:
            for i in range(1, self._mv_device_combo.count()):
                d = self._mv_device_combo.itemData(i)
                if d and d["universe"] == mv_cfg.get("universe") and d["start_channel"] == mv_cfg.get("start_channel"):
                    self._mv_device_combo.setCurrentIndex(i)
                    break
        self._mv_device_combo.currentIndexChanged.connect(self._on_mv_device_changed)
        self._prop_layout.addRow("Device:", self._mv_device_combo)

        # Channel mapping combos for movement roles
        self._mv_ch_container = QtWidgets.QWidget()
        self._mv_ch_layout = QtWidgets.QFormLayout(self._mv_ch_container)
        self._mv_ch_layout.setContentsMargins(0, 0, 0, 0)
        self._mv_ch_layout.setVerticalSpacing(3)
        self._prop_layout.addRow(self._mv_ch_container)
        self._mv_combos: dict[MovementRole, QtWidgets.QComboBox] = {}
        self._rebuild_mv_combos(obj)

        self._add_separator()

        # Color Device (RGB/W)
        self._add_section_header("Color Device (RGB)")
        self._col_device_combo = QtWidgets.QComboBox(self._prop_container)
        self._col_device_combo.addItem("(None)", None)
        for fix in self._used_fixtures:
            self._col_device_combo.addItem(fixture_label(fix), _fixture_combo_data(fix))

        # Pre-select the matching device if already configured
        self._col_device_combo.setCurrentIndex(0)
        col_cfg = dc.get("color")
        if col_cfg:
            for i in range(1, self._col_device_combo.count()):
                d = self._col_device_combo.itemData(i)
                if (
                    d
                    and d["universe"] == col_cfg.get("universe")
                    and d["start_channel"] == col_cfg.get("start_channel")
                ):
                    self._col_device_combo.setCurrentIndex(i)
                    break
        self._col_device_combo.currentIndexChanged.connect(self._on_col_device_changed)
        self._prop_layout.addRow("Device:", self._col_device_combo)

        # Channel mapping combos for color roles
        self._col_ch_container = QtWidgets.QWidget()
        self._col_ch_layout = QtWidgets.QFormLayout(self._col_ch_container)
        self._col_ch_layout.setContentsMargins(0, 0, 0, 0)
        self._col_ch_layout.setVerticalSpacing(3)
        self._prop_layout.addRow(self._col_ch_container)
        self._col_combos: dict[ColorRole, QtWidgets.QComboBox] = {}
        self._rebuild_col_combos(obj)

    def _rebuild_mv_combos(self, obj: StageObject) -> None:
        """Rebuild the movement channel mapping combo boxes."""
        while self._mv_ch_layout.rowCount() > 0:
            self._mv_ch_layout.removeRow(0)
        self._mv_combos.clear()
        device_data = self._mv_device_combo.currentData()
        if not device_data:
            return
        ch_names = device_data.get("channel_names", [])
        dc = (obj.device_config or {}).get("movement", {})
        mapping = dc.get("mapping") or auto_detect_mapping(ch_names, MovementRole)

        labels = {
            MovementRole.PAN_COARSE: "Pan:",
            MovementRole.PAN_FINE: "Pan fine:",
            MovementRole.TILT_COARSE: "Tilt:",
            MovementRole.TILT_FINE: "Tilt fine:",
            MovementRole.DIMMER: "Dimmer:",
            MovementRole.PAN_TILT_SPEED: "P/T Speed:",
        }
        for role in MovementRole:
            combo = QtWidgets.QComboBox(self._mv_ch_container)
            combo.addItem("(None)", -1)
            for idx, cn in enumerate(ch_names):
                combo.addItem(f"CH{idx}: {cn}", idx)
            # Pre-select the mapped channel
            cur = mapping.get(role.value, -1)
            if cur >= 0:
                for ci in range(1, combo.count()):
                    if combo.itemData(ci) == cur:
                        combo.setCurrentIndex(ci)
                        break
            combo.currentIndexChanged.connect(lambda _idx, r=role: self._on_mv_mapping_changed(r))
            self._mv_ch_layout.addRow(labels.get(role, role), combo)
            self._mv_combos[role] = combo

    def _rebuild_col_combos(self, obj: StageObject) -> None:
        """Rebuild the color channel mapping combo boxes."""
        while self._col_ch_layout.rowCount() > 0:
            self._col_ch_layout.removeRow(0)
        self._col_combos.clear()
        device_data = self._col_device_combo.currentData()
        if not device_data:
            return
        ch_names = device_data.get("channel_names", [])
        dc = (obj.device_config or {}).get("color", {})
        mapping = dc.get("mapping") or auto_detect_mapping(ch_names, ColorRole)

        labels = {
            ColorRole.RED: "Red:",
            ColorRole.GREEN: "Green:",
            ColorRole.BLUE: "Blue:",
            ColorRole.WHITE: "White:",
        }
        for role in ColorRole:
            combo = QtWidgets.QComboBox(self._col_ch_container)
            combo.addItem("(None)", -1)
            for idx, cn in enumerate(ch_names):
                combo.addItem(f"CH{idx}: {cn}", idx)
            cur = mapping.get(role.value, -1)
            if cur >= 0:
                for ci in range(1, combo.count()):
                    if combo.itemData(ci) == cur:
                        combo.setCurrentIndex(ci)
                        break
            combo.currentIndexChanged.connect(lambda _idx, r=role: self._on_col_mapping_changed(r))
            self._col_ch_layout.addRow(labels.get(role, role), combo)
            self._col_combos[role] = combo

    def _on_mv_device_changed(self, _: int) -> None:  # Index argument is not required
        if self._updating_ui or not self._current_obj:
            return
        dd = self._mv_device_combo.currentData()
        if self._current_obj.device_config is None:
            self._current_obj.device_config = {}
        if dd is None:
            self._current_obj.device_config.pop("movement", None)
        else:
            mapping = auto_detect_mapping(dd["channel_names"], MovementRole)
            self._current_obj.device_config["movement"] = {
                "universe": dd["universe"],
                "start_channel": dd["start_channel"],
                "channel_count": dd["channel_count"],
                "mapping": mapping,
            }
        self._updating_ui = True
        self._rebuild_mv_combos(self._current_obj)
        self._updating_ui = False
        self._refresh_locks()
        self._emit_changed()

    def _on_col_device_changed(self, _: int) -> None:  # Provided index argument is not required
        if self._updating_ui or not self._current_obj:
            return
        dd = self._col_device_combo.currentData()
        if self._current_obj.device_config is None:
            self._current_obj.device_config = {}
        if dd is None:
            self._current_obj.device_config.pop("color", None)
        else:
            mapping = auto_detect_mapping(dd["channel_names"], ColorRole)
            self._current_obj.device_config["color"] = {
                "universe": dd["universe"],
                "start_channel": dd["start_channel"],
                "channel_count": dd["channel_count"],
                "mapping": mapping,
            }
        self._updating_ui = True
        self._rebuild_col_combos(self._current_obj)
        self._updating_ui = False
        self._refresh_locks()
        self._emit_changed()

    def _on_mv_mapping_changed(self, role: MovementRole) -> None:
        if self._updating_ui or not self._current_obj:
            return
        dc = self._current_obj.device_config
        if not dc or "movement" not in dc:
            return
        combo = self._mv_combos.get(role)
        if combo:
            dc["movement"]["mapping"][role.value] = combo.currentData()
        self._refresh_locks()
        self._emit_changed()

    def _on_col_mapping_changed(self, role: ColorRole) -> None:
        if self._updating_ui or not self._current_obj:
            return
        dc = self._current_obj.device_config
        if not dc or "color" not in dc:
            return
        combo = self._col_combos.get(role)
        if combo:
            dc["color"]["mapping"][role.value] = combo.currentData()
        self._refresh_locks()
        self._emit_changed()

    # Fixture change handlers

    def _emit_changed(self) -> None:
        """Notify the mediator that the current fixture's properties changed."""
        if self._updating_ui or not self._current_obj:
            return
        self.object_changed.emit(self._current_obj.id)

    def _on_name_changed(self, text: str) -> None:
        if self._updating_ui or not self._current_obj:
            return
        self._current_obj.name = text.strip()
        # Update the list item text for the selected fixture
        for item in self._fixture_list.selectedItems():
            oid = item.data(ROLE_ID)
            if oid == self._current_obj.id and not item.data(ROLE_IS_GROUP):
                grp = self._stage_config.get_group_for_fixture(oid)
                if grp:
                    item.setText(f"    \u2514 {self._display_text(self._current_obj)}")
                else:
                    item.setText(self._display_text(self._current_obj))
        self._emit_changed()

    @staticmethod
    def _spin_triplet(spins: list[QtWidgets.QDoubleSpinBox]) -> tuple[float, float, float]:
        """Read exactly three spin boxes into a fixed-size 3-tuple."""
        if len(spins) != 3:
            raise ValueError(f"_spin_triplet expects exactly three spin boxes, got {len(spins)}.")
        return spins[0].value(), spins[1].value(), spins[2].value()

    def _on_position_changed(self) -> None:
        if self._updating_ui or not self._current_obj:
            return
        self._current_obj.position = self._spin_triplet(self._pos_spins)
        self._emit_changed()

    def _on_rotation_changed(self) -> None:
        if self._updating_ui or not self._current_obj:
            return
        self._current_obj.rotation = self._spin_triplet(self._rot_spins)
        self._emit_changed()

    def _on_scale_changed(self, val: float | str) -> None:
        if self._updating_ui or not self._current_obj:
            return
        self._current_obj.scale = float(val)
        self._emit_changed()

    def _on_attr(self, attr: str, val: float | str) -> None:
        """Handle simple float attribute (pan, tilt, dimmer) changes."""
        if self._updating_ui or not self._current_obj:
            return
        setattr(self._current_obj, attr, float(val))
        self._emit_changed()

    def _on_beam_toggled(self, state: bool) -> None:
        if self._updating_ui or not isinstance(self._current_obj, (MovingHead, ParCan)):
            return
        self._current_obj.beam_on = bool(state)
        self._emit_changed()

    def _on_dimmer_slider(self, val: float) -> None:
        """Synchronize the dimmer slider with the spin box."""
        if self._updating_ui or not isinstance(self._current_obj, (MovingHead, ParCan)):
            return
        v = val / 100.0
        self._current_obj.dimmer = v
        self._updating_ui = True
        self._dimmer_spin.setValue(v)
        self._updating_ui = False
        self._emit_changed()

    def _on_rgb_changed(self) -> None:
        if self._updating_ui or not isinstance(self._current_obj, (MovingHead, ParCan)):
            return
        r, g, b = (s.value() for s in self._rgb_spins)
        self._current_obj.beam_color = (r, g, b)
        self._update_color_btn_style(r, g, b)
        self._emit_changed()

    def _on_color_picker(self) -> None:
        """Open a QColorDialog and apply the chosen color."""
        if not isinstance(self._current_obj, (MovingHead, ParCan)):
            return
        r, g, b = self._current_obj.beam_color
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(r, g, b), self, "Beam Color")
        if color.isValid():
            nr, ng, nb = color.red(), color.green(), color.blue()
            self._updating_ui = True
            self._rgb_spins[0].setValue(nr)
            self._rgb_spins[1].setValue(ng)
            self._rgb_spins[2].setValue(nb)
            self._updating_ui = False
            self._current_obj.beam_color = (nr, ng, nb)
            self._update_color_btn_style(nr, ng, nb)
            self._emit_changed()

    # Group change handlers

    def _on_group_name_changed(self, text: str) -> None:
        """Rename the selected group."""
        if self._updating_ui or not self._current_group:
            return
        self._current_group.name = text.strip()
        for item in self._fixture_list.selectedItems():
            if item.data(ROLE_IS_GROUP) and item.data(ROLE_ID) == self._current_group.id:
                item.setText(self._group_display_text(self._current_group))
        self._emit_group_changed()

    def _on_group_position_changed(self) -> None:
        """Translate all group members by the same delta as the group center."""
        if self._updating_ui or not self._current_group:
            return
        old_pos = self._current_group.position
        new_pos = self._spin_triplet(self._pos_spins)
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]
        dz = new_pos[2] - old_pos[2]
        self._current_group.position = new_pos

        # Apply the same translation delta to all member fixtures
        for mid in self._current_group.member_ids:
            obj = self._stage_config.get_object(mid)
            if obj:
                obj.position = (
                    obj.position[0] + dx,
                    obj.position[1] + dy,
                    obj.position[2] + dz,
                )

        self._emit_group_changed()

    def _on_group_rotation_changed(self) -> None:
        """Rotate all members around the group center using total rotation."""
        if self._updating_ui or not self._current_group:
            return

        new_rot = self._spin_triplet(self._rot_spins)

        # Total rotation relative to the snapshot baseline
        base = self._group_base_rotation
        total_rx = new_rot[0] - base[0]
        total_ry = new_rot[1] - base[1]
        total_rz = new_rot[2] - base[2]
        self._current_group.rotation = new_rot

        cx, cy, cz = self._current_group.position

        for mid in self._current_group.member_ids:
            if mid not in self._group_base_offsets:
                continue
            (ox, oy, oz), base_rot = self._group_base_offsets[mid]

            # Apply total rotation to the original offset (X then Y then Z)
            rx, ry, rz = ox, oy, oz

            # Rotation around X axis
            if abs(total_rx) > 1e-9:
                rad = math.radians(total_rx)
                c, s = math.cos(rad), math.sin(rad)
                ry2 = ry * c - rz * s
                rz2 = ry * s + rz * c
                ry, rz = ry2, rz2

            # Rotation around Y axis
            if abs(total_ry) > 1e-9:
                rad = math.radians(total_ry)
                c, s = math.cos(rad), math.sin(rad)
                rx2 = rx * c + rz * s
                rz2 = -rx * s + rz * c
                rx, rz = rx2, rz2

            # Rotation around Z axis
            if abs(total_rz) > 1e-9:
                rad = math.radians(total_rz)
                c, s = math.cos(rad), math.sin(rad)
                rx2 = rx * c - ry * s
                ry2 = rx * s + ry * c
                rx, ry = rx2, ry2

            obj = self._stage_config.get_object(mid)
            if obj:
                obj.position = (cx + rx, cy + ry, cz + rz)
                obj.rotation = (
                    base_rot[0] + total_rx,
                    base_rot[1] + total_ry,
                    base_rot[2] + total_rz,
                )

        self._emit_group_changed()

    def _emit_group_changed(self) -> None:
        """Notify that group member objects changed (triggers 3D update + save)."""
        if self._updating_ui or not self._current_group:
            return
        for mid in self._current_group.member_ids:
            self.object_changed.emit(mid)

    # Actions (Add / Remove / Group)

    def _on_add_clicked(self) -> None:
        """Open the fixture selection dialog and adds the selected fixtures."""
        existing = self._stage_config.get_all_names()
        dlg = AddFixtureDialog(existing, self._used_fixtures, self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        self.add_object_requested.emit(dlg.selected_fixture_key(), dlg.selected_name(), dlg.selected_device())

    def _on_remove_clicked(self) -> None:
        """Remove the selected fixture from the stage."""
        selected_items = self._fixture_list.selectedItems()
        if not selected_items:
            return
        for item in list(selected_items):
            oid = item.data(ROLE_ID)
            is_group = item.data(ROLE_IS_GROUP)
            if not oid:
                continue
            if is_group:
                self.remove_group_requested.emit(oid)
            else:
                self.remove_object_requested.emit(oid)

    def _on_group_clicked(self) -> None:
        """Group all selected non-group fixtures together."""
        selected_items = self._fixture_list.selectedItems()
        fixture_ids = []
        for item in selected_items:
            if not item.data(ROLE_IS_GROUP):
                oid = item.data(ROLE_ID)
                if oid:
                    fixture_ids.append(oid)
        if len(fixture_ids) < 2:
            return

        existing = self._stage_config.get_all_names()
        dlg = GroupNameDialog(existing, self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        self.group_requested.emit(fixture_ids, dlg.selected_name())

    # API

    def add_object_to_list(self, obj: StageObject) -> None:
        """Add a newly created fixture to the list widget."""
        if obj.get_type() == "platform":
            return
        item = QtWidgets.QListWidgetItem(self._display_text(obj))
        item.setData(ROLE_ID, obj.id)
        item.setData(ROLE_IS_GROUP, False)
        self._fixture_list.addItem(item)
        self._fixture_list.clearSelection()
        item.setSelected(True)
        self._fixture_list.scrollToItem(item)

    def remove_object_from_list(self, object_id: str) -> None:
        """Remove a fixture from the list widget by ID."""
        for i in range(self._fixture_list.count()):
            item = self._fixture_list.item(i)
            if item and item.data(ROLE_ID) == object_id:
                self._fixture_list.takeItem(i)
                break

    def refresh_list(self) -> None:
        """Full rebuild of the fixture list."""
        self._rebuild_list()

    def select_fixture_by_id(self, object_id: str) -> None:
        """Select a fixture in the list by its object ID (from left-click)."""
        for i in range(self._fixture_list.count()):
            item = self._fixture_list.item(i)
            if item and item.data(ROLE_ID) == object_id and not item.data(ROLE_IS_GROUP):
                self._fixture_list.clearSelection()
                item.setSelected(True)
                self._fixture_list.scrollToItem(item)
                return

    def deselect_all(self) -> None:
        """Clear selection entirely (from right-click)."""
        self._fixture_list.clearSelection()

    def set_stage_config(self, stage_config: StageConfig) -> None:
        """Swap the stage configuration and rebuild the fixture list.

        Resets the selection and group bookkeeping, which still referred to
        objects of the previous stage.
        """
        self._stage_config = stage_config
        self._current_obj = None
        self._current_group = None
        self._group_base_offsets = {}
        self.refresh_list()

    def set_used_fixtures(self, used_fixtures: list[UsedFixture] | None) -> None:
        """Update the selectable DMX devices.

        Rebuilds the property panel when a moving head is selected, so its
        device combos no longer show the fixtures of the previous show file.
        """
        self._used_fixtures = used_fixtures or []
        if isinstance(self._current_obj, (MovingHead, ParCan, PixelFixture)):
            self._build_properties(self._current_obj)

    def dmx_live_enabled(self) -> bool:
        """Whether the user enabled live DMX reception (the "DMX Live" checkbox)."""
        return self._dmx_cb.isChecked()
