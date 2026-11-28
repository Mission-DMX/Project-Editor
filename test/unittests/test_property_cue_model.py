"""Unit tests for the property-cue model persistence layer (WP7)."""

from __future__ import annotations

import unittest
from logging import getLogger

from model.color_hsi import ColorHSI
from model.virtual_filters.property_cues.distribution import Distribution, DistributionMethod
from model.virtual_filters.property_cues.model import (
    EnabledCapability,
    EndAction,
    FixtureSelection,
    FixtureSelectionEntry,
    ManualPropertyAssignment,
    PresetPropertyAssignment,
    PropertyAssignments,
    PropertyCue,
    PropertyCueFilterModel,
    PropertyStep,
    SelectionEntryKind,
)

logger = getLogger(__name__)


class PropertyCueModelRoundTripTest(unittest.TestCase):
    """Verify JSON serialisation round-trips for the PropertyCueFilterModel."""

    def test_default_roundtrip(self) -> None:
        """Verify an empty default model survives a JSON round trip unchanged."""
        model = PropertyCueFilterModel()
        blob = model.to_json_str()
        loaded = PropertyCueFilterModel.from_json_str(blob)
        self.assertEqual(model, loaded)

    def test_populated_roundtrip(self) -> None:
        """Verify a fully populated model preserves every field through JSON round trip."""
        fixture_entry = FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")
        selection = FixtureSelection(
            entries=[fixture_entry],
            enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.POSITION},
        )
        manual = ManualPropertyAssignment(
            values={"brightness": 0.75, "strobefreq": 0.0},
            distribution=Distribution(
                method=DistributionMethod.PHASE_LINEAR,
                phase_offset=0.5,
                amplitude=1.0,
            ),
            transition="sig",
        )
        preset = PresetPropertyAssignment(
            preset_id="circle",
            hint_values={"radius": 0.3, "color": ColorHSI(120.0, 1.0, 0.5)},
            distribution=Distribution(
                method=DistributionMethod.PHASE_SIN,
                phase_offset=1.5,
                amplitude=2.0,
                introduction_delay_only=True,
            ),
        )
        assignments = PropertyAssignments(
            by_property={"dimmer": manual, "position": preset},
        )
        step = PropertyStep(
            name="Step 1",
            duration_40hz=80,
            fade_in_40hz=20,
            assignments={"fixture:MH1": assignments},
        )
        cue = PropertyCue(name="My cue", steps=[step],
                          end_action=EndAction.NEXT, restart_on_play=True)
        model = PropertyCueFilterModel(
            fixture_selection=selection,
            cues=[cue],
        )
        model.general.default_cue_index = 0

        blob = model.to_json_str()
        loaded = PropertyCueFilterModel.from_json_str(blob)
        self.assertEqual(model.general, loaded.general)
        self.assertEqual(model.fixture_selection, loaded.fixture_selection)
        self.assertEqual(len(model.cues), len(loaded.cues))
        self.assertEqual(cue.end_action, loaded.cues[0].end_action)
        self.assertEqual(cue.restart_on_play, loaded.cues[0].restart_on_play)
        loaded_step = loaded.cues[0].steps[0]
        self.assertEqual(step.name, loaded_step.name)
        self.assertEqual(step.duration_40hz, loaded_step.duration_40hz)
        self.assertEqual(step.fade_in_40hz, loaded_step.fade_in_40hz)
        loaded_assignments = loaded_step.assignments["fixture:MH1"]
        loaded_manual = loaded_assignments.by_property["dimmer"]
        self.assertIsInstance(loaded_manual, ManualPropertyAssignment)
        self.assertEqual(manual.values, loaded_manual.values)
        self.assertEqual(manual.distribution, loaded_manual.distribution)
        self.assertEqual(manual.transition, loaded_manual.transition)
        loaded_preset = loaded_assignments.by_property["position"]
        self.assertIsInstance(loaded_preset, PresetPropertyAssignment)
        self.assertEqual(preset.preset_id, loaded_preset.preset_id)
        self.assertEqual(preset.distribution, loaded_preset.distribution)
        self.assertEqual(set(preset.hint_values.keys()), set(loaded_preset.hint_values.keys()))
        self.assertEqual(preset.hint_values["radius"], loaded_preset.hint_values["radius"])
        loaded_color = loaded_preset.hint_values["color"]
        self.assertIsInstance(loaded_color, ColorHSI)
        self.assertAlmostEqual(preset.hint_values["color"].hue, loaded_color.hue)
        self.assertAlmostEqual(preset.hint_values["color"].saturation, loaded_color.saturation)
        self.assertAlmostEqual(preset.hint_values["color"].intensity, loaded_color.intensity)

    def test_load_from_json_str_mutates_in_place(self) -> None:
        """Loading must keep the model's object identity so UI widgets stay bound."""
        model = PropertyCueFilterModel()
        original_id = id(model)
        model.load_from_json_str(
            '{"version": 1, "fixture_selection": {"entries": [], "enabled_capabilities": []},'
            ' "general": {}, "cues": [{"name": "Loaded", "steps": []}]}',
        )
        self.assertEqual(original_id, id(model))
        self.assertEqual(1, len(model.cues))
        self.assertEqual("Loaded", model.cues[0].name)

    def test_load_from_json_str_empty_resets_contents(self) -> None:
        """Verify loading an empty JSON string clears pre-existing cues on the model."""
        model = PropertyCueFilterModel()
        model.cues.append(PropertyCue(name="To be dropped"))
        model.load_from_json_str("")
        self.assertEqual([], model.cues)

    def test_version_rejects(self) -> None:
        """Verify deserialising an unsupported schema version raises ValueError."""
        with self.assertRaises(ValueError):
            PropertyCueFilterModel.from_json_str('{"version": 99, "fixture_selection": {}, "cues": []}')

    def test_empty_string_loads_default(self) -> None:
        """Verify deserialising an empty string yields the default model."""
        loaded = PropertyCueFilterModel.from_json_str("")
        default = PropertyCueFilterModel()
        self.assertEqual(default, loaded)

    def test_load_from_json_str_rejects_unsupported_schema_version_atomically(self) -> None:
        """Regression: a bad schema version leaves the model untouched."""
        model = PropertyCueFilterModel()
        from model.virtual_filters.property_cues.model import (
            FixtureSelection,
            FixtureSelectionEntry,
            SelectionEntryKind,
        )
        model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="orig")],
            enabled_capabilities=set(),
        )
        with self.assertRaises(ValueError):
            model.load_from_json_str('{"version": 9999, "cues": []}')
        self.assertEqual(
            "orig", model.fixture_selection.entries[0].id,
            "A failed load must not have touched self.fixture_selection",
        )


class FixtureSelectionDiffTest(unittest.TestCase):
    """Verify FixtureSelection.diff returns added and removed entries correctly."""

    def test_fixture_selection_diff(self) -> None:
        """Verify diff computes added and removed entries between two selections."""
        entry_a = FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="A")
        entry_b = FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="B")
        entry_c = FixtureSelectionEntry(kind=SelectionEntryKind.GROUP, id="MovingHeads")
        before = FixtureSelection(entries=[entry_a, entry_b])
        after = FixtureSelection(entries=[entry_a, entry_c])
        added, removed = before.diff(after)
        self.assertEqual([entry_c], added)
        self.assertEqual([entry_b], removed)


class CopyFromNeighbourTest(unittest.TestCase):
    """Verify copy_fixture_from_neighbour clones assignments from the right neighbour fixture."""

    def _build_model_with_fixture(self, fixture_path: str, values: dict | None = None) -> PropertyCueFilterModel:
        model = PropertyCueFilterModel()
        manual = ManualPropertyAssignment(values=values if values is not None else {"brightness": 0.9})
        step = PropertyStep(
            name="s1",
            assignments={fixture_path: PropertyAssignments(by_property={"dimmer": manual})},
        )
        cue = PropertyCue(name="cue", steps=[step])
        model.cues.append(cue)
        return model

    def test_copy_from_neighbour_same_group(self) -> None:
        """Verify copying from a neighbour in the same group clones its assignments deeply."""
        model = self._build_model_with_fixture("group:MovingHeads/fixture:MH1")
        memberships = {
            "MH1": ["MovingHeads"],
            "MH2": ["MovingHeads"],
        }
        model.copy_fixture_from_neighbour("group:MovingHeads/fixture:MH2", memberships)
        step = model.cues[0].steps[0]
        self.assertIn("group:MovingHeads/fixture:MH2", step.assignments)
        copied = step.assignments["group:MovingHeads/fixture:MH2"].by_property["dimmer"]
        self.assertIsInstance(copied, ManualPropertyAssignment)
        self.assertEqual({"brightness": 0.9}, copied.values)
        # Verify deep copy
        source = step.assignments["group:MovingHeads/fixture:MH1"].by_property["dimmer"]
        source.values["brightness"] = 0.1
        self.assertEqual(0.9, copied.values["brightness"])

    def test_copy_from_neighbour_falls_back_to_first(self) -> None:
        """Verify copying falls back to the first existing fixture when no neighbour shares a group."""
        model = self._build_model_with_fixture("fixture:A")
        memberships = {
            "A": [],
            "B": ["OtherGroup"],
        }
        model.copy_fixture_from_neighbour("fixture:B", memberships)
        step = model.cues[0].steps[0]
        self.assertIn("fixture:B", step.assignments)
        copied = step.assignments["fixture:B"].by_property["dimmer"]
        self.assertIsInstance(copied, ManualPropertyAssignment)
        self.assertEqual({"brightness": 0.9}, copied.values)

    def test_copy_from_neighbour_no_fixtures(self) -> None:
        """Verify copying is a no-op when there are no existing fixture assignments to clone from."""
        model = PropertyCueFilterModel()
        step = PropertyStep(name="empty", assignments={})
        model.cues.append(PropertyCue(name="cue", steps=[step]))
        model.copy_fixture_from_neighbour("fixture:newcomer", {"newcomer": []})
        self.assertEqual({}, model.cues[0].steps[0].assignments)


if __name__ == "__main__":
    unittest.main()
