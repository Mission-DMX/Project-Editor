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
        emissions: list[tuple[int, str, str]] = []
        tree.selection_changed.connect(
            lambda si, np, pid: emissions.append((si, np, pid)),
        )
        child = tree.topLevelItem(0).child(0)
        tree._on_item_clicked(child, 2)
        self.assertEqual(1, len(emissions))
        step_index, node_path, prop_id = emissions[0]
        self.assertEqual("dimmer", prop_id)
        self.assertEqual("fixture:F1", node_path)
        self.assertEqual(0, step_index)


@unittest.skipUnless(_HAS_PYSIDE, "PySide6 required")
class PropertyPaneTests(unittest.TestCase):

    def _make_pane(self):
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import (
            PropertyPane,
        )
        model = _make_model(fixture_ids=["F1"], cue_specs=[[("s0", 40, 0)]])
        pane = PropertyPane(model)
        pane.set_current_cue(0)
        return model, pane

    def test_property_pane_switches_editor(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.editors.dimmer_editor import (
            DimmerEditor,
        )
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.editors.position_editor import (
            PositionEditor,
        )
        _, pane = self._make_pane()
        pane.show_editor(0, "fixture:F1", "dimmer")
        self.assertIsInstance(pane.current_editor(), DimmerEditor)
        pane.show_editor(0, "fixture:F1", "position")
        self.assertIsInstance(pane.current_editor(), PositionEditor)

    def test_apply_dimmer_writes_model(self) -> None:
        from model.virtual_filters.property_cues.model.property_step import (
            ManualPropertyAssignment,
        )
        model, pane = self._make_pane()
        pane.show_editor(0, "fixture:F1", "dimmer")
        editor = pane.current_editor()
        editor._brightness.setValue(0.75)
        editor._on_apply()
        bucket = model.cues[0].steps[0].assignments["fixture:F1"]
        assignment = bucket.by_property["dimmer"]
        self.assertIsInstance(assignment, ManualPropertyAssignment)
        self.assertEqual(0.75, assignment.values["brightness"])

    def test_apply_preset_writes_model(self) -> None:
        from model.virtual_filters.property_cues.model.property_step import (
            PresetPropertyAssignment,
        )
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
            pane.show_editor(0, "fixture:F1", "dimmer")
            editor = pane.current_editor()
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
        pane.show_editor(0, "fixture:F1", "dimmer")
        editor = pane.current_editor()
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

    def test_step_editor_edits_timing(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.editors.step_editor import (
            StepEditor,
        )
        model, pane = self._make_pane()
        pane.show_editor(0, "", "")
        editor = pane.current_editor()
        self.assertIsInstance(editor, StepEditor)
        editor._duration.setValue(120)
        editor._on_apply()
        self.assertEqual(120, model.cues[0].steps[0].duration_40hz)


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
