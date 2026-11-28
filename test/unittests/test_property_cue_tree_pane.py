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
    """Re-enable the garbage collector after the module finishes."""
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
    """Tests for the StepFixtureTree widget's model-driven rebuild and selection."""

    def test_tree_rebuilds_from_model(self) -> None:
        """Verify the tree rebuilds its top-level items when switching cues."""
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
        """Verify selection_changed emits step index and node path on item clicks."""
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

    def test_frost_column_is_present(self) -> None:
        """Regression: the tree must include a Frost summary column."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import (
            StepFixtureTree,
            _COLUMNS,
        )
        self.assertIn("Frost", _COLUMNS)
        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        tree = StepFixtureTree(model)
        self.assertEqual(len(_COLUMNS), tree.columnCount())

    def test_keyboard_selection_also_emits(self) -> None:
        """Regression: keyboard navigation (currentItemChanged) emits selection_changed."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import (
            StepFixtureTree,
        )
        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0), ("s1", 40, 0)]])
        tree = StepFixtureTree(model)
        tree.set_current_cue(0)
        emissions: list[tuple[int, str]] = []
        tree.selection_changed.connect(lambda si, np: emissions.append((si, np)))
        # setCurrentItem fires currentItemChanged which the tree now handles.
        tree.setCurrentItem(tree.topLevelItem(1))
        self.assertIn((1, ""), emissions)

    def test_select_step_programmatic(self) -> None:
        """Regression: select_step moves the selection to (cue, step)."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import (
            StepFixtureTree,
        )
        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0), ("s1", 40, 0), ("s2", 40, 0)]])
        tree = StepFixtureTree(model)
        tree.set_current_cue(0)
        tree.select_step(0, 2)
        self.assertEqual(2, tree.current_step_index())

    def test_fixture_name_resolver(self) -> None:
        """Verify the name_resolver callback is used when rendering fixture rows."""
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
        """Verify the summary columns render the assigned property values."""
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
    """Tests for the PropertyPane widget's editors and persistence."""

    def _make_pane(self, enabled_capabilities: set | None = None):
        """Return a built model and PropertyPane configured with given capabilities."""
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
        """Verify all property tabs are shown when all capabilities are enabled."""
        _, pane = self._make_pane()
        pane.show_editor(0, "fixture:F1")
        self.assertEqual(7, pane._tabs.count())
        self.assertFalse(pane._placeholder.isVisibleTo(pane))

    def test_capability_filter_disables_unavailable_tabs(self) -> None:
        """Verify tabs for disabled capabilities are hidden from the user."""
        from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability
        _, pane = self._make_pane(enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.COLOR})
        self.assertTrue(pane._tabs.isTabEnabled(pane._tab_indices["dimmer"]))
        self.assertTrue(pane._tabs.isTabEnabled(pane._tab_indices["color"]))
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
        model.fixture_selection.enabled_capabilities = {EnabledCapability.GOBO, EnabledCapability.COLOR}

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
        self.assertTrue(pane._tabs.isTabEnabled(pane._tab_indices["color"]))

        pane.show_editor(0, "fixture:SPOT")
        self.assertTrue(pane._tabs.isTabEnabled(pane._tab_indices["gobo"]))
        self.assertFalse(pane._tabs.isTabEnabled(pane._tab_indices["color"]))

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

    def test_gobo_editor_restores_slots_after_json_roundtrip(self) -> None:
        """Verify the gobo editor restores slot selections after a JSON string-key roundtrip.

        A JSON-roundtripped assignment turns int keys into strings; the editor
        must still restore the user's slot selection.
        """
        from unittest.mock import MagicMock
        from model.ofl.ofl_fixture import WheelSlotType
        from model.virtual_filters.property_cues.model.property_step import (
            ManualPropertyAssignment,
            PropertyAssignments,
        )
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.editors.gobo_editor import GoboEditor

        def _slot(stype: WheelSlotType, name: str) -> MagicMock:
            s = MagicMock(); s.type = stype; s.name = name; s.pixmap.return_value = None
            return s

        wheel = MagicMock(); wheel.slots = [
            _slot(WheelSlotType.OPEN, "Open"),
            _slot(WheelSlotType.GOBO, "A"),
            _slot(WheelSlotType.GOBO, "B"),
            _slot(WheelSlotType.GOBO, "C"),
        ]
        fixture = MagicMock()
        fixture._fixture = MagicMock(); fixture._fixture.wheels = {"W": wheel}

        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        model.cues[0].steps[0].assignments["fixture:F1"] = PropertyAssignments(
            by_property={
                "gobo": ManualPropertyAssignment(
                    values={
                        "wheel_count": 1,
                        # Simulate the JSON-roundtripped shape: str keys.
                        "slots": {"0": 2},
                        "rotations": {"0": 0.3},
                    },
                ),
            },
        )
        editor = GoboEditor(model)
        editor.set_fixtures([fixture])
        editor.load(0, 0, "fixture:F1")
        self.assertEqual(2, editor._wheel_blocks[0].slot_combo.currentIndex())
        self.assertAlmostEqual(0.3, editor._wheel_blocks[0].rotation.value(), places=4)

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
        """Verify applying the dimmer editor writes a ManualPropertyAssignment to the model."""
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
        """Verify applying a preset writes a PresetPropertyAssignment to the model."""
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

    def test_preset_hint_values_survive_reload(self) -> None:
        """Regression: editing a preset hint used to revert to the spec default.

        ``PresetPanel.set_selected_preset`` only moved the combo cursor; the
        ``_rebuild_hints`` slot then seeded every hint widget from
        :attr:`PresetHintSpec.default`, so the saved ``hint_values`` from the
        model were silently overridden with the spec default (e.g. ``speed=60``)
        on every re-open of the step. The panel now takes the saved hint values
        and writes them into the widgets after the rebuild.
        """
        from model.virtual_filters.property_cues.model.property_step import PresetPropertyAssignment
        from model.virtual_filters.property_cues.presets.loader import load_preset_library
        with tempfile.TemporaryDirectory() as tmp:
            preset_blob = {
                "name": "SwellTest",
                "description": "test",
                "applies_for": "dimmer",
                "hints": [{"id": "speed", "type": "float", "default": 60.0}],
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
            # Simulate the user dialing the hint away from its default.
            editor._preset_panel._hint_widgets["speed"].setValue(30.0)
            editor._on_apply()

            bucket = model.cues[0].steps[0].assignments["fixture:F1"]
            assignment = bucket.by_property["dimmer"]
            self.assertIsInstance(assignment, PresetPropertyAssignment)
            self.assertEqual({"speed": 30.0}, assignment.hint_values)

            # Navigate away and back: loading the step must restore the saved
            # 30.0 into the widget, not the hint's default 60.0.
            pane.show_editor(0, "")
            pane.show_editor(0, "fixture:F1")
            self.assertEqual(
                30.0, editor._preset_panel._hint_widgets["speed"].value(),
            )

    def test_distribution_controls_write(self) -> None:
        """Verify distribution controls persist into the assignment on apply."""
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
        """Verify duration and fade-in values entered in seconds persist as 40Hz ticks."""
        model, pane = self._make_pane()
        pane.show_editor(0, "")
        self.assertIs(pane._step_editor, pane._top_stack.currentWidget())
        editor = pane._step_editor
        editor._duration.setValue(3.0)
        editor._fade_in.setValue(0.5)
        # No manual apply call: the editor auto-applies on every
        # ``valueChanged`` so the model picks the edits up straight away.
        self.assertEqual(120, model.cues[0].steps[0].duration_40hz)
        self.assertEqual(20, model.cues[0].steps[0].fade_in_40hz)

    def test_step_editor_auto_applies_without_apply_button(self) -> None:
        """Regression: ``_duration`` / ``_fade_in`` / ``_name_edit`` auto-persist.

        The former behaviour required the user to click an Apply button;
        closing the dialog without pressing it left ``duration_40hz`` at the
        default (1 s) even after the user had typed, e.g., ``10`` into the
        duration spinbox. This test pins the model-side effect of each of the
        three signals the editor now connects.
        """
        model, pane = self._make_pane()
        pane.show_editor(0, "")
        editor = pane._step_editor

        editor._duration.setValue(10.0)
        self.assertEqual(400, model.cues[0].steps[0].duration_40hz)

        editor._fade_in.setValue(0.25)
        self.assertEqual(10, model.cues[0].steps[0].fade_in_40hz)

        editor._name_edit.setText("Entry")
        # ``editingFinished`` only fires on focus-out / Enter, so emit it
        # explicitly here to mirror the Qt side of a committed edit.
        editor._name_edit.editingFinished.emit()
        self.assertEqual("Entry", model.cues[0].steps[0].name)

    def test_step_level_dimmer_writes_assignment(self) -> None:
        """Verify applying the dimmer editor at the step level writes to the empty node path."""
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
    """Integration tests for the PropertyCueEditor top-level widget."""

    def _make_editor(self):
        """Return a fresh filter and PropertyCueEditor instance for integration tests."""
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
        """Verify the editor's splitter hosts the live step tree and property pane widgets."""
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
