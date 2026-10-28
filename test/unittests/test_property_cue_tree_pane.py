"""Unit tests for WP11 property-cue step tree and property pane."""

from __future__ import annotations

import gc
import importlib.util
import json
import sys
import tempfile
import unittest
from logging import getLogger

_HAS_PYSIDE = importlib.util.find_spec("PySide6") is not None

logger = getLogger(__name__)

_qapp = None


def setUpModule() -> None:  # noqa: N802
    """Create a shared QApplication so widgets can be instantiated in tests."""
    global _qapp
    if not _HAS_PYSIDE:
        return
    from PySide6.QtWidgets import QApplication
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def tearDownModule() -> None:  # noqa: N802
    gc.enable()


def _make_model(fixture_ids: list[str], cue_specs: list[list[tuple[str, int, int]]]):
    """Build a model with ``fixture_ids`` selected and cues with the given steps."""
    from model.virtual_filters.property_cues.model import (
        PropertyCue,
        PropertyCueFilterModel,
        PropertyStep,
    )
    from model.virtual_filters.property_cues.model.fixture_selection import (
        FixtureSelection,
        FixtureSelectionEntry,
        SelectionEntryKind,
    )
    selection = FixtureSelection(
        entries=[
            FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=fid)
            for fid in fixture_ids
        ],
        enabled_capabilities=set(),
    )
    cues: list[PropertyCue] = []
    for cue_steps in cue_specs:
        steps = [
            PropertyStep(name=name, duration_40hz=duration, fade_in_40hz=fade)
            for name, duration, fade in cue_steps
        ]
        cues.append(PropertyCue(name="Cue", steps=steps))
    return PropertyCueFilterModel(fixture_selection=selection, cues=cues)


@unittest.skipUnless(_HAS_PYSIDE, "PySide6 required")
class StepFixtureTreeTests(unittest.TestCase):

    def test_tree_rebuilds_from_model(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import (
            StepFixtureTree,
        )
        model = _make_model(
            fixture_ids=["F1"],
            cue_specs=[
                [("s0", 40, 0), ("s1", 80, 0)],
                [("t0", 40, 0), ("t1", 40, 0), ("t2", 40, 0)],
            ],
        )
        tree = StepFixtureTree(model)
        tree.set_current_cue(0)
        self.assertEqual(2, tree.topLevelItemCount())
        self.assertEqual(1, tree.topLevelItem(0).childCount())
        tree.set_current_cue(1)
        self.assertEqual(3, tree.topLevelItemCount())

    def test_selection_signal(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import (
            StepFixtureTree,
        )
        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        tree = StepFixtureTree(model)
        tree.set_current_cue(0)
        emissions: list[tuple[int, str]] = []
        tree.selection_changed.connect(lambda si, np: emissions.append((si, np)))
        child = tree.topLevelItem(0).child(0)
        tree._on_item_clicked(child, 0)
        self.assertEqual([(0, "fixture:F1")], emissions)
        tree._on_item_clicked(tree.topLevelItem(0), 0)
        self.assertEqual([(0, "fixture:F1"), (0, "")], emissions)

    def test_fixture_name_resolver(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import (
            StepFixtureTree,
        )
        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        resolver = lambda kind, raw: {"fixture": {"F1": "Mover 1"}}.get(kind, {}).get(raw, raw)
        tree = StepFixtureTree(model, name_resolver=resolver)
        tree.set_current_cue(0)
        child = tree.topLevelItem(0).child(0)
        self.assertEqual("Mover 1", child.text(0))

    def test_summary_columns_display_assignment_values(self) -> None:
        from model.virtual_filters.property_cues.distribution import Distribution
        from model.virtual_filters.property_cues.model.property_step import (
            ManualPropertyAssignment,
            PropertyAssignments,
        )
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import (
            StepFixtureTree,
        )
        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        step = model.cues[0].steps[0]
        step.assignments["fixture:F1"] = PropertyAssignments(
            by_property={
                "dimmer": ManualPropertyAssignment(
                    values={"brightness": 0.75}, distribution=Distribution(),
                ),
            },
        )
        tree = StepFixtureTree(model)
        tree.set_current_cue(0)
        child = tree.topLevelItem(0).child(0)
        # Column 2 is the Dimmer column.
        self.assertEqual("0.75", child.text(2))
        # Other columns stay as "-" until something is assigned.
        self.assertEqual("-", child.text(3))


@unittest.skipUnless(_HAS_PYSIDE, "PySide6 required")
class PropertyPaneTests(unittest.TestCase):

    def _make_pane(self, enabled_capabilities: set | None = None):
        from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import (
            PropertyPane,
        )
        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        if enabled_capabilities is None:
            enabled_capabilities = set(EnabledCapability)
        model.fixture_selection.enabled_capabilities = set(enabled_capabilities)
        pane = PropertyPane(model)
        pane.set_current_cue(0)
        return model, pane

    def test_property_pane_shows_all_tabs(self) -> None:
        _, pane = self._make_pane()
        pane.show_editor(0, "fixture:F1")
        self.assertEqual(7, pane._tabs.count())
        self.assertFalse(pane._placeholder.isVisibleTo(pane))

    def test_capability_filter_disables_unavailable_tabs(self) -> None:
        from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability
        _, pane = self._make_pane(enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.COLOUR})
        self.assertTrue(pane._tabs.isTabEnabled(pane._tab_indices["dimmer"]))
        self.assertTrue(pane._tabs.isTabEnabled(pane._tab_indices["colour"]))
        self.assertFalse(pane._tabs.isTabEnabled(pane._tab_indices["position"]))
        self.assertFalse(pane._tabs.isTabEnabled(pane._tab_indices["beam"]))

    def test_gobo_tab_disabled_for_fixture_without_gobo_wheel(self) -> None:
        """A fixture whose wheels contain no GOBO slots must disable the Gobo tab."""
        from unittest.mock import MagicMock
        from model.ofl.ofl_fixture import WheelSlotType
        from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import PropertyPane

        colour_slot = MagicMock(); colour_slot.type = WheelSlotType.COLOR
        colour_wheel = MagicMock(); colour_wheel.slots = [colour_slot]
        wash_fixture = MagicMock()
        wash_fixture._fixture = MagicMock(); wash_fixture._fixture.wheels = {"Colour Wheel": colour_wheel}
        wash_fixture.fixture_channels = ()

        gobo_slot = MagicMock(); gobo_slot.type = WheelSlotType.GOBO
        gobo_slot.name = "Dot"; gobo_slot.pixmap.return_value = None
        gobo_wheel = MagicMock(); gobo_wheel.slots = [gobo_slot]
        spot_fixture = MagicMock()
        spot_fixture._fixture = MagicMock(); spot_fixture._fixture.wheels = {"Gobo Wheel": gobo_wheel}
        spot_fixture.fixture_channels = ()

        model = _make_model(fixture_ids=["WASH", "SPOT"], cue_specs=[[("s0", 40, 0)]])
        model.fixture_selection.enabled_capabilities = {EnabledCapability.GOBO, EnabledCapability.COLOUR}

        def lookup(node_path: str):
            if node_path == "fixture:WASH":
                return [wash_fixture]
            if node_path == "fixture:SPOT":
                return [spot_fixture]
            return []

        pane = PropertyPane(model, fixture_lookup=lookup)
        pane.set_current_cue(0)

        pane.show_editor(0, "fixture:WASH")
        self.assertFalse(pane._tabs.isTabEnabled(pane._tab_indices["gobo"]))
        self.assertTrue(pane._tabs.isTabEnabled(pane._tab_indices["colour"]))

        pane.show_editor(0, "fixture:SPOT")
        self.assertTrue(pane._tabs.isTabEnabled(pane._tab_indices["gobo"]))
        self.assertFalse(pane._tabs.isTabEnabled(pane._tab_indices["colour"]))

    def test_gobo_editor_rebuilt_from_fixture_slots(self) -> None:
        """set_fixtures replaces the fallback with one sub-block per gobo wheel."""
        from unittest.mock import MagicMock
        from model.ofl.ofl_fixture import WheelSlotType
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.editors.gobo_editor import GoboEditor

        def _slot(stype: WheelSlotType, name: str) -> MagicMock:
            s = MagicMock(); s.type = stype; s.name = name; s.pixmap.return_value = None
            return s

        open_slot = _slot(WheelSlotType.OPEN, "Open")
        swirl = _slot(WheelSlotType.GOBO, "Swirl")
        gobo_wheel = MagicMock(); gobo_wheel.slots = [open_slot, swirl]
        rot_open = _slot(WheelSlotType.OPEN, "Open")
        rot_dot = _slot(WheelSlotType.GOBO, "Dot")
        rot_star = _slot(WheelSlotType.GOBO, "Star")
        rot_gobo_wheel = MagicMock(); rot_gobo_wheel.slots = [rot_open, rot_dot, rot_star]
        fixture = MagicMock()
        fixture._fixture = MagicMock()
        fixture._fixture.wheels = {"Gobo Wheel": gobo_wheel, "Rotatable Gobo Wheel": rot_gobo_wheel}

        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        editor = GoboEditor(model)
        # Default: one generic 16-slot wheel.
        self.assertEqual(1, len(editor._wheel_blocks))
        self.assertEqual(16, editor._wheel_blocks[0].slot_combo.count())
        editor.set_fixtures([fixture])
        self.assertEqual(2, len(editor._wheel_blocks))
        self.assertEqual(2, editor._wheel_blocks[0].slot_combo.count())
        self.assertEqual(3, editor._wheel_blocks[1].slot_combo.count())
        self.assertEqual("Gobo Wheel", editor._wheel_blocks[0].group.title())
        self.assertEqual("Rotatable Gobo Wheel", editor._wheel_blocks[1].group.title())
        self.assertEqual("0: Open", editor._wheel_blocks[0].slot_combo.itemText(0))
        self.assertEqual("1: Dot", editor._wheel_blocks[1].slot_combo.itemText(1))

    def test_refresh_preserves_tree_selection(self) -> None:
        """``StepFixtureTree.refresh`` must not drop the user's selection."""
        from PySide6.QtCore import Qt
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import StepFixtureTree

        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0), ("s1", 40, 0)]])
        tree = StepFixtureTree(model)
        tree.set_current_cue(0)
        step0 = tree.topLevelItem(0)
        tree.setCurrentItem(step0.child(0))
        tree.refresh()
        self.assertEqual(2, tree.topLevelItemCount())
        current = tree.currentItem()
        self.assertIsNotNone(current)
        self.assertEqual("fixture:F1", current.data(0, Qt.ItemDataRole.UserRole + 2))
        self.assertEqual(0, current.data(0, Qt.ItemDataRole.UserRole + 1))

    def test_apply_does_not_clear_tree(self) -> None:
        """Pressing Apply refreshes the summary columns but keeps items and selection."""
        from PySide6.QtCore import Qt
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import PropertyPane
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import StepFixtureTree

        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        pane = PropertyPane(model, fixture_lookup=lambda _np: [])
        pane.set_current_cue(0)
        tree = StepFixtureTree(model)
        tree.set_current_cue(0)
        pane.assignment_applied.connect(tree.refresh)
        fixture_item = tree.topLevelItem(0).child(0)
        tree.setCurrentItem(fixture_item)
        pane.show_editor(0, "fixture:F1")
        editor = pane._editors["dimmer"]
        editor._brightness.setValue(0.6)
        editor._on_apply()
        # Tree still has its item; selection is still on the fixture row.
        self.assertEqual(1, tree.topLevelItemCount())
        current = tree.currentItem()
        self.assertIsNotNone(current)
        self.assertEqual("fixture:F1", current.data(0, Qt.ItemDataRole.UserRole + 2))
        # And the summary column reflects the applied value.
        self.assertEqual("0.60", current.text(2))

    def test_gobo_editor_apply_writes_per_wheel_values(self) -> None:
        """Applying with multiple wheels stores slots/rotations per wheel index."""
        from unittest.mock import MagicMock
        from model.ofl.ofl_fixture import WheelSlotType
        from model.virtual_filters.property_cues.model.property_step import ManualPropertyAssignment
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.editors.gobo_editor import GoboEditor

        def _slot(stype: WheelSlotType, name: str) -> MagicMock:
            s = MagicMock(); s.type = stype; s.name = name; s.pixmap.return_value = None
            return s

        wheel_a = MagicMock(); wheel_a.slots = [_slot(WheelSlotType.OPEN, "Open"), _slot(WheelSlotType.GOBO, "A")]
        wheel_b = MagicMock(); wheel_b.slots = [_slot(WheelSlotType.OPEN, "Open"), _slot(WheelSlotType.GOBO, "B")]
        fixture = MagicMock()
        fixture._fixture = MagicMock(); fixture._fixture.wheels = {"W1": wheel_a, "W2": wheel_b}

        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        model.cues[0].steps[0].assignments.clear()
        editor = GoboEditor(model)
        editor.set_fixtures([fixture])
        editor._cue_index = 0; editor._step_index = 0; editor._node_path = "fixture:F1"
        editor._wheel_blocks[0].slot_combo.setCurrentIndex(1)
        editor._wheel_blocks[0].rotation.setValue(0.5)
        editor._wheel_blocks[1].slot_combo.setCurrentIndex(1)
        editor._wheel_blocks[1].rotation.setValue(-0.25)
        editor._on_apply()
        bucket = model.cues[0].steps[0].assignments["fixture:F1"]
        assignment = bucket.by_property["gobo"]
        self.assertIsInstance(assignment, ManualPropertyAssignment)
        self.assertEqual(2, assignment.values["wheel_count"])
        self.assertEqual({0: 1, 1: 1}, assignment.values["slots"])
        self.assertEqual({0: 0.5, 1: -0.25}, assignment.values["rotations"])

    def test_apply_dimmer_writes_model(self) -> None:
        from model.virtual_filters.property_cues.model.property_step import ManualPropertyAssignment
        model, pane = self._make_pane()
        pane.show_editor(0, "fixture:F1")
        editor = pane._editors["dimmer"]
        editor._brightness.setValue(0.75)
        editor._on_apply()
        bucket = model.cues[0].steps[0].assignments["fixture:F1"]
        assignment = bucket.by_property["dimmer"]
        self.assertIsInstance(assignment, ManualPropertyAssignment)
        self.assertEqual(0.75, assignment.values["brightness"])

    def test_apply_preset_writes_model(self) -> None:
        from model.virtual_filters.property_cues.model.property_step import PresetPropertyAssignment
        from model.virtual_filters.property_cues.presets.loader import load_preset_library
        with tempfile.TemporaryDirectory() as tmp:
            preset_blob = {
                "name": "SwellTest",
                "description": "test",
                "applies_for": "dimmer",
                "hints": [{"id": "speed", "type": "float", "default": 1.0}],
                "kf_requests": [
                    {"duration": "{{ speed }}", "channels": {"brightness": "1.0"}},
                ],
            }
            with open(f"{tmp}/swell.json", "w", encoding="utf-8") as fh:
                json.dump(preset_blob, fh)
            library = load_preset_library(builtin_dir=tmp, user_dir=tmp)
            model, pane = self._make_pane()
            pane.show_editor(0, "fixture:F1")
            editor = pane._editors["dimmer"]
            editor._preset_panel.set_library(library)
            editor._mode.set_manual(False)
            editor._preset_panel.set_selected_preset("SwellTest")
            editor._on_apply()
        bucket = model.cues[0].steps[0].assignments["fixture:F1"]
        assignment = bucket.by_property["dimmer"]
        self.assertIsInstance(assignment, PresetPropertyAssignment)
        self.assertEqual("SwellTest", assignment.preset_id)

    def test_distribution_controls_write(self) -> None:
        from model.virtual_filters.property_cues.distribution import DistributionMethod
        model, pane = self._make_pane()
        pane.show_editor(0, "fixture:F1")
        editor = pane._editors["dimmer"]
        editor._brightness.setValue(0.5)
        for i in range(editor._distribution._method.count()):
            if editor._distribution._method.itemData(i) == DistributionMethod.PHASE_SIN:
                editor._distribution._method.setCurrentIndex(i)
                break
        editor._distribution._phase_offset.setValue(0.3)
        editor._on_apply()
        bucket = model.cues[0].steps[0].assignments["fixture:F1"]
        assignment = bucket.by_property["dimmer"]
        self.assertEqual(DistributionMethod.PHASE_SIN, assignment.distribution.method)
        self.assertAlmostEqual(0.3, assignment.distribution.phase_offset, places=5)

    def test_step_editor_edits_timing_in_seconds(self) -> None:
        model, pane = self._make_pane()
        pane.show_editor(0, "")
        self.assertIs(pane._step_editor, pane._top_stack.currentWidget())
        editor = pane._step_editor
        editor._duration.setValue(3.0)
        editor._fade_in.setValue(0.5)
        editor._on_apply()
        self.assertEqual(120, model.cues[0].steps[0].duration_40hz)
        self.assertEqual(20, model.cues[0].steps[0].fade_in_40hz)

    def test_step_level_dimmer_writes_assignment(self) -> None:
        from model.virtual_filters.property_cues.model.property_step import ManualPropertyAssignment
        model, pane = self._make_pane()
        pane.show_editor(0, "")  # select the step row
        editor = pane._editors["dimmer"]
        editor._brightness.setValue(0.5)
        editor._on_apply()
        bucket = model.cues[0].steps[0].assignments[""]
        self.assertIsInstance(bucket.by_property["dimmer"], ManualPropertyAssignment)
        self.assertEqual(0.5, bucket.by_property["dimmer"].values["brightness"])


@unittest.skipUnless(_HAS_PYSIDE, "PySide6 required")
class PropertyCueEditorIntegrationTests(unittest.TestCase):

    def _make_editor(self):
        from model import BoardConfiguration, Scene
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )
        show = BoardConfiguration()
        scene = Scene(0, "Test property-cue tree-pane scene", show)
        show._add_scene(scene)
        f = PropertyBasedCueFilter(scene, "pcf_tree_pane")
        editor = PropertyCueEditor(f=f)
        return f, editor

    def test_splitter_hosts_live_panes(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import (
            PropertyPane,
        )
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import (
            StepFixtureTree,
        )
        _, editor = self._make_editor()
        self.assertIsInstance(editor._step_tree, StepFixtureTree)
        self.assertIsInstance(editor._property_pane, PropertyPane)


if __name__ == "__main__":
    unittest.main()
