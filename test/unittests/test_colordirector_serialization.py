"""Unit tests for the color director filter serialization.

These tests cover the serialization of color presets, color groups and recalls as well as the filter message
handling paths that do not require a network connection or a running fish instance.

"""

import unittest

from model import BoardConfiguration, DataType, Scene
from model.color_hsi import ColorHSI
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.colordirector_vfilter import (
    _ACCENT_COLOR_DELIMITER,
    _ASSET_DELIMITER,
    _FIELD_DELIMITER,
    _LIST_ELEMENT_DELIMITER,
    _MAX_RECALL_COUNT,
    _PRESET_DELIMITER,
    _RECALL_DELIMITER,
    _RECALL_STATE_DELIMITER,
    _sanitize_channel_name,
    STEP_DURATION_MS,
    ColorPreset,
    ColordirectorVFilter,
    bound_preset_index,
    is_valid_channel_name,
)


class _FakeFilterUpdateMessage:
    """Duck typed replacement for proto.FilterMode_pb2.update_parameter messages."""

    def __init__(self, filter_id: str, parameter_value: str) -> None:
        self.filter_id = filter_id
        self.parameter_value = parameter_value


class ColorPresetSerializationTest(unittest.TestCase):
    """Serialization tests for single color presets."""

    def test_empty_preset_serializes_to_empty_string(self):
        """An empty preset serializes to an empty string and back."""
        self.assertEqual(ColorPreset().serialize(), "")
        self.assertEqual(ColorPreset.from_filter_str("").colors, [])

    def test_single_step_round_trip(self):
        """A single fade in step survives a serialization round trip."""
        preset = ColorPreset.from_filter_str("12|lin|120.0,0.5,0.75")
        self.assertEqual(len(preset.colors), 1)
        duration, transfer_function, colors = preset.colors[0]
        self.assertEqual(duration, 12)
        self.assertIs(transfer_function, TransferFunction.LINEAR)
        self.assertEqual([color.format_for_filter() for color in colors], ["120.0,0.5,0.75"])
        self.assertEqual(preset.serialize(), "12|lin|120.0,0.5,0.75")

    def test_multiple_steps_round_trip(self):
        """Multiple fade in steps keep their order and values."""
        preset = ColorPreset.from_filter_str("3|e_i|10.0,0.25,0.5#7|sig|200.0,0.8,0.9")
        self.assertEqual([step[0] for step in preset.colors], [3, 7])
        self.assertEqual([step[1] for step in preset.colors], [TransferFunction.EASE_IN, TransferFunction.SIGMOIDAL])
        self.assertEqual(preset.serialize(), "3|e_i|10.0,0.25,0.5#7|sig|200.0,0.8,0.9")

    def test_all_transfer_functions_round_trip(self):
        """All transfer function identifiers survive a serialization round trip."""
        for transfer_function in TransferFunction:
            with self.subTest(transfer_function=transfer_function):
                preset = ColorPreset.from_filter_str(f"5|{transfer_function.value}|1.0,0.2,0.3")
                self.assertEqual(len(preset.colors), 1)
                self.assertIs(preset.colors[0][1], transfer_function)
                self.assertEqual(preset.serialize(), f"5|{transfer_function.value}|1.0,0.2,0.3")

    def test_step_without_accent_colors_round_trip(self):
        """Steps without accent colors keep an empty color list and serialize stably."""
        preset = ColorPreset.from_filter_str("12|lin|")
        self.assertEqual(preset.colors, [(12, TransferFunction.LINEAR, [])])
        self.assertEqual(preset.serialize(), "12|lin|")

    def test_multiple_accent_colors_round_trip(self):
        """All accent colors of a step survive a serialization round trip."""
        preset = ColorPreset.from_filter_str("4|edg|10.0,0.25,0.5@300.0,0.75,1.0")
        self.assertEqual(len(preset.colors), 1)
        self.assertEqual(
            [color.format_for_filter() for color in preset.colors[0][2]],
            ["10.0,0.25,0.5", "300.0,0.75,1.0"],
        )
        self.assertEqual(preset.serialize(), "4|edg|10.0,0.25,0.5@300.0,0.75,1.0")

    def test_malformed_duration_is_ignored(self):
        """Steps with a non integer duration are ignored."""
        self.assertEqual(ColorPreset.from_filter_str("ab|lin|1.0,0.2,0.3").colors, [])

    def test_step_with_wrong_field_count_is_ignored(self):
        """Steps that do not provide exactly three fields are ignored."""
        self.assertEqual(ColorPreset.from_filter_str("12|lin").colors, [])
        self.assertEqual(ColorPreset.from_filter_str("12|lin|1.0,0.2,0.3|extra").colors, [])

    def test_unparsable_accent_color_is_ignored(self):
        """Steps with an unparsable accent color are ignored completely."""
        self.assertEqual(ColorPreset.from_filter_str("12|lin|x,y,z").colors, [])

    def test_accent_color_without_commas_is_ignored(self):
        """Steps with accent colors without the expected comma separation are ignored completely."""
        self.assertEqual(ColorPreset.from_filter_str("12|lin|abc").colors, [])

    def test_asset_uuid_prefix_round_trip(self):
        """An unresolvable asset uuid prefix is preserved on serialization."""
        preset = ColorPreset.from_filter_str("123e4567?12|lin|120.0,0.5,0.75")
        self.assertIsNone(preset.visualization_asset)
        self.assertEqual(preset.serialize(), "123e4567?12|lin|120.0,0.5,0.75")

    def test_asset_uuid_without_steps_round_trip(self):
        """A preset that only consists of an asset uuid survives a round trip."""
        preset = ColorPreset.from_filter_str("xyz?")
        self.assertIsNone(preset.visualization_asset)
        self.assertEqual(preset.serialize(), "xyz?")

    def test_get_button_visualization_uses_default_color_for_empty_steps(self):
        """Steps without accent colors are represented by the default button color."""
        preset = ColorPreset.from_filter_str("12|lin|120.0,0.5,0.75#5|edg|")
        self.assertEqual(
            [color.format_for_filter() for color in preset.get_button_visualization()],
            ["120.0,0.5,0.75", "128.0,0.5,1.0"],
        )


class ColorHSIParsingTest(unittest.TestCase):
    """Tests for the strict and lenient color parsing modes used by the color presets."""

    def test_lenient_parsing_falls_back_to_default(self):
        """Malformed color strings fall back to the default color if strict mode is not requested."""
        for filter_format in ("", "1.0,2.0"):
            with self.subTest(filter_format=filter_format):
                self.assertEqual(ColorHSI.from_filter_str(filter_format).format_for_filter(), "128.0,0.5,1.0")

    def test_strict_parsing_raises_value_error(self):
        """Malformed color strings raise a ValueError in strict mode."""
        for filter_format in ("", "1.0,2.0", "x,y,z"):
            with self.subTest(filter_format=filter_format):
                with self.assertRaises(ValueError):
                    ColorHSI.from_filter_str(filter_format, strict=True)


class ChannelNameTest(unittest.TestCase):
    """Tests for color group and sub output name handling."""

    def test_valid_channel_names_are_accepted(self):
        """Names of ascii letters, digits, single underscores and hyphens are valid."""
        for name in ("a", "A1", "Group-1", "sub_out2", "a-b_c"):
            with self.subTest(name=name):
                self.assertTrue(is_valid_channel_name(name))

    def test_invalid_channel_names_are_rejected(self):
        """Empty names and names containing problematic characters are invalid."""
        for name in ("", "a b", "a:b", "a#b", "a|b", "a__b", "a_", "_", "a?b", "\u00e4"):
            with self.subTest(name=name):
                self.assertFalse(is_valid_channel_name(name))

    def test_sanitize_channel_name(self):
        """Sanitizing removes problematic characters and collapses double underscores."""
        self.assertEqual(_sanitize_channel_name(" a:b#c|d e__f "), "abcd_e-f")

    def test_sanitize_channel_name_replaces_consecutive_spaces_by_hyphen(self):
        """Consecutive spaces turn into double underscores which collapse into a single hyphen."""
        self.assertEqual(_sanitize_channel_name("a  b"), "a-b")

    def test_sanitize_channel_name_replacement_order_matters(self):
        """Triple underscores become a hyphen followed by an underscore, matching the serialized name."""
        sanitized = _sanitize_channel_name("a___b")
        self.assertEqual(sanitized, "a-_b")
        self.assertEqual(_sanitize_channel_name(sanitized), sanitized)


class BoundPresetIndexTest(unittest.TestCase):
    """Tests for bounding color preset indices."""

    def test_valid_preset_indices_are_returned(self):
        """Indices addressing an available preset are returned unchanged."""
        self.assertEqual(bound_preset_index(0, 3), 0)
        self.assertEqual(bound_preset_index(2, 3), 2)

    def test_invalid_preset_indices_are_bounded_to_zero(self):
        """Negative and too large indices are bounded to the first preset."""
        self.assertEqual(bound_preset_index(-1, 3), 0)
        self.assertEqual(bound_preset_index(3, 3), 0)


class _ColorDirectorTestBase(unittest.TestCase):
    """Base class providing a builder for deserialized color director filters."""

    @staticmethod
    def _make_director(color_groups: str = "", presets: str = "", recalls: str = "") -> ColordirectorVFilter:
        """Create a color director filter with the provided serialized configuration values."""
        show = BoardConfiguration()
        scene = Scene(0, "Color director test scene", show)
        show._add_scene(scene)
        director = ColordirectorVFilter(scene, "colordirector")
        director.filter_configurations["colorgroups"] = color_groups
        director.filter_configurations["presets"] = presets
        director.filter_configurations["recalls"] = recalls
        director.deserialize()
        return director


class ColorDirectorSerializationTest(_ColorDirectorTestBase):
    """Serialization tests for the color director filter configuration."""

    def test_empty_filter_is_empty(self):
        """A filter without configuration values contains no groups, presets or recalls."""
        director = self._make_director()
        self.assertEqual(director.output_groups, {})
        self.assertEqual(director.presets, [])
        self.assertEqual(director.recalls, [])
        self.assertEqual(director.get_outputs(), [])

    def test_color_groups_round_trip(self):
        """Color groups survive a serialization round trip and outputs are sorted."""
        director = self._make_director(color_groups="group1|r|g|b#group2|w")
        self.assertEqual(director.output_groups, {"group1": ["r", "g", "b"], "group2": ["w"]})
        self.assertEqual(director.get_outputs(), ["group1__b", "group1__g", "group1__r", "group2__w"])
        director.serialize()
        self.assertEqual(director.filter_configurations["colorgroups"], "group1|r|g|b#group2|w")

    def test_color_groups_ignore_invalid_names(self):
        """Color groups with invalid names are ignored while deserializing."""
        director = self._make_director(color_groups="ok|a#_|b")
        self.assertEqual(director.output_groups, {"ok": ["a"]})

    def test_color_groups_ignore_duplicate_names(self):
        """Color groups using an already used name are ignored while deserializing."""
        director = self._make_director(color_groups="dup|a#dup|b")
        self.assertEqual(director.output_groups, {"dup": ["a"]})

    def test_color_group_names_are_sanitized(self):
        """Color group and sub output names are sanitized while deserializing."""
        director = self._make_director(color_groups="my group|my chan")
        self.assertEqual(director.output_groups, {"my_group": ["my_chan"]})

    def test_out_data_types_are_populated(self):
        """Every sub output provides a color typed out data entry."""
        director = self._make_director(color_groups="g|a|b")
        self.assertEqual(director.out_data_types, {"g__a": DataType.DT_COLOR, "g__b": DataType.DT_COLOR})

    def test_presets_configuration_round_trip(self):
        """The presets configuration survives a serialization round trip."""
        director = self._make_director(presets="12|lin|120.0,0.5,0.75$4|edg|10.0,0.2,0.3")
        self.assertEqual(len(director.presets), 2)
        director.serialize()
        self.assertEqual(director.filter_configurations["presets"], "12|lin|120.0,0.5,0.75$4|edg|10.0,0.2,0.3")

    def test_malformed_preset_keeps_empty_preset(self):
        """A malformed preset deserializes to an empty preset that serializes to nothing."""
        director = self._make_director(presets="bogus")
        self.assertEqual(len(director.presets), 1)
        self.assertEqual(director.presets[0].colors, [])
        director.serialize()
        self.assertEqual(director.filter_configurations["presets"], "")

    def test_recalls_round_trip(self):
        """Recalls survive a serialization round trip."""
        director = self._make_director(recalls="0,1;2,3")
        self.assertEqual(director.recalls, [[0, 1], [2, 3]])
        director.serialize()
        self.assertEqual(director.filter_configurations["recalls"], "0,1;2,3")

    def test_malformed_recall_states_default_to_zero(self):
        """Non integer recall states deserialize to zero."""
        director = self._make_director(recalls="0,x,2;1")
        self.assertEqual(director.recalls, [[0, 0, 2], [1]])
        director.serialize()
        self.assertEqual(director.filter_configurations["recalls"], "0,0,2;1")

    def test_normalize_recall_pads_and_truncates(self):
        """Recalls are adjusted to the number of color groups and unknown indices are ignored."""
        padded = self._make_director(color_groups="g|a#h|b", recalls="1")
        padded.normalize_recall(0)
        self.assertEqual(padded.recalls[0], [1, 0])

        truncated = self._make_director(color_groups="g|a#h|b", recalls="1,2,3")
        truncated.normalize_recall(0)
        self.assertEqual(truncated.recalls[0], [1, 2])
        truncated.normalize_recall(9)
        self.assertEqual(truncated.recalls[0], [1, 2])

    def test_remove_output_group_adjusts_recalls(self):
        """Removing a color group removes its entries from the recalls; unknown names are ignored."""
        director = self._make_director(color_groups="g|a#h|b#i|c", recalls="0,1,2")
        director.remove_output_group("h")
        self.assertEqual(director.output_groups, {"g": ["a"], "i": ["c"]})
        self.assertEqual(director.recalls, [[0, 2]])
        director.remove_output_group("unknown")
        self.assertEqual(director.recalls, [[0, 2]])

    def test_full_configuration_round_trip(self):
        """A full configuration survives a serialization round trip."""
        director = self._make_director(
            color_groups="group1|r|g#group2|w",
            presets="12|lin|120.0,0.5,0.75$4|edg|10.0,0.2,0.3",
            recalls="0,1;2,3",
        )
        director.serialize()
        self.assertEqual(director.filter_configurations["colorgroups"], "group1|r|g#group2|w")
        self.assertEqual(director.filter_configurations["presets"], "12|lin|120.0,0.5,0.75$4|edg|10.0,0.2,0.3")
        self.assertEqual(director.filter_configurations["recalls"], "0,1;2,3")

    def test_serialization_delimiters_are_pairwise_distinct(self):
        """All serialization delimiters differ from each other."""
        delimiters = {
            _PRESET_DELIMITER,
            _LIST_ELEMENT_DELIMITER,
            _FIELD_DELIMITER,
            _ACCENT_COLOR_DELIMITER,
            _ASSET_DELIMITER,
            _RECALL_DELIMITER,
            _RECALL_STATE_DELIMITER,
        }
        self.assertEqual(len(delimiters), 7)


class ColorDirectorMessageTest(_ColorDirectorTestBase):
    """Tests for filter message handling that does not require a network connection."""

    def test_unknown_message_key_is_rejected(self):
        """Unknown message keys are rejected."""
        director = self._make_director()
        self.assertFalse(director.handle_filter_message("bogus", "1"))

    def test_save_selection_rejects_non_integer_values(self):
        """Save selection messages with non integer recall indices are rejected."""
        director = self._make_director()
        self.assertFalse(director.handle_filter_message("save-selection-to-recall", "x"))

    def test_save_selection_rejects_out_of_range_targets(self):
        """Save selection messages targeting more than the maximum recall count are rejected."""
        director = self._make_director()
        self.assertFalse(director.handle_filter_message("save-selection-to-recall", str(_MAX_RECALL_COUNT)))

    def test_save_selection_rejects_empty_selection(self):
        """Save selection messages without an active selection are rejected."""
        director = self._make_director(color_groups="g|a")
        self.assertFalse(director.handle_filter_message("save-selection-to-recall", "0"))

    def test_update_active_colors_ignores_unknown_filters(self):
        """Cue filter updates of unknown filters are ignored."""
        director = self._make_director(color_groups="g|a", presets="12|lin|120.0,0.5,0.75")
        director._update_active_colors_from_filters(_FakeFilterUpdateMessage("unknown", "run;0"))
        self.assertEqual(director.get_current_active_colors(), [])

    def test_update_active_colors_ignores_invalid_values(self):
        """Malformed cue filter updates and invalid preset indices are ignored."""
        director = self._make_director(color_groups="g|a#h|b", presets="12|lin|120.0,0.5,0.75")
        director._cue_filter_to_group_index_mapping["colordirector__cue__g"] = 0
        for value in ("run", "run;x", "run;9"):
            with self.subTest(value=value):
                director._update_active_colors_from_filters(_FakeFilterUpdateMessage("colordirector__cue__g", value))
        self.assertEqual(director.get_current_active_colors(), [])

    def test_save_selection_stores_current_colors(self):
        """Save selection messages store the active colors and grow the recall list."""
        director = self._make_director(color_groups="g|a#h|b", presets="12|lin|120.0,0.5,0.75$4|edg|10.0,0.2,0.3")
        director._cue_filter_to_group_index_mapping["colordirector__cue__g"] = 0
        director._update_active_colors_from_filters(_FakeFilterUpdateMessage("colordirector__cue__g", "run;1"))
        self.assertEqual(director.get_current_active_colors(), [1, 0])
        self.assertTrue(director.handle_filter_message("save-selection-to-recall", "0"))
        self.assertEqual(director.recalls, [[1, 0]])
        self.assertTrue(director.handle_filter_message("save-selection-to-recall", "1"))
        self.assertEqual(director.recalls, [[1, 0], [1, 0]])

    def test_recall_rejects_unknown_indices(self):
        """Recall messages with unknown recall indices are rejected."""
        director = self._make_director(color_groups="g|a", recalls="0,1")
        self.assertFalse(director.handle_filter_message("recall", "5"))

    def test_recall_rejects_missing_presets(self):
        """Recall messages are rejected if the filter does not provide presets."""
        director = self._make_director(color_groups="g|a", recalls="0,1")
        self.assertFalse(director.handle_filter_message("recall", "0"))

    def test_recall_rejects_non_integer_values(self):
        """Recall messages with non integer recall indices are rejected."""
        director = self._make_director(color_groups="g|a", recalls="0,1")
        self.assertFalse(director.handle_filter_message("recall", "x"))

    def test_call_rejects_unknown_groups(self):
        """Call messages targeting unknown color groups are rejected."""
        director = self._make_director(color_groups="grp|a", presets="12|lin|120.0,0.5,0.75")
        self.assertFalse(director.handle_filter_message("call", "bogus,0"))

    def test_call_rejects_invalid_preset_indices(self):
        """Call messages with invalid preset indices are rejected."""
        director = self._make_director(color_groups="grp|a", presets="12|lin|120.0,0.5,0.75")
        self.assertFalse(director.handle_filter_message("call", "grp,1"))

    def test_call_rejects_malformed_values(self):
        """Call messages without a group and preset index pair are rejected."""
        director = self._make_director(color_groups="grp|a", presets="12|lin|120.0,0.5,0.75")
        self.assertFalse(director.handle_filter_message("call", "grp"))
        self.assertFalse(director.handle_filter_message("call", "grp,x"))

    def test_call_column_rejects_invalid_preset_indices(self):
        """Call column messages with invalid preset indices are rejected."""
        director = self._make_director(color_groups="grp|a", presets="12|lin|120.0,0.5,0.75")
        self.assertFalse(director.handle_filter_message("call-column", "1"))

    def test_call_column_rejects_malformed_values(self):
        """Call column messages with non integer preset indices are rejected."""
        director = self._make_director(color_groups="grp|a", presets="12|lin|120.0,0.5,0.75")
        self.assertFalse(director.handle_filter_message("call-column", "x"))


class RecallSelectionTest(_ColorDirectorTestBase):
    """Tests for resolving the color preset selection stored by recalls."""

    def test_selection_contains_an_entry_per_group(self):
        """The selection resolves the stored preset index of every color group."""
        director = self._make_director(
            color_groups="g|a#h|b", presets="12|lin|120.0,0.5,0.75$4|edg|10.0,0.2,0.3", recalls="1,0"
        )
        self.assertEqual(director.get_recall_preset_selection(0), [("g", 1), ("h", 0)])

    def test_selection_bounds_invalid_stored_indices(self):
        """Stored indices that do not address a preset are bounded to the first preset and logged."""
        director = self._make_director(color_groups="g|a", presets="12|lin|120.0,0.5,0.75", recalls="7")
        with self.assertLogs("model.virtual_filters.colordirector_vfilter", level="WARNING"):
            self.assertEqual(director.get_recall_preset_selection(0), [("g", 0)])

    def test_selection_pads_short_recalls(self):
        """Missing entries of short recalls default to the first color preset."""
        director = self._make_director(
            color_groups="g|a#h|b", presets="12|lin|120.0,0.5,0.75$4|edg|10.0,0.2,0.3", recalls="1"
        )
        self.assertEqual(director.get_recall_preset_selection(0), [("g", 1), ("h", 0)])

    def test_selection_rejects_unknown_recall_indices(self):
        """Unknown recall indices resolve to None."""
        director = self._make_director(color_groups="g|a", presets="12|lin|120.0,0.5,0.75", recalls="0")
        self.assertIsNone(director.get_recall_preset_selection(1))

    def test_selection_rejects_missing_presets(self):
        """The selection resolves to None if the filter does not provide presets."""
        director = self._make_director(color_groups="g|a", recalls="0")
        self.assertIsNone(director.get_recall_preset_selection(0))


class PopulatePresetsTest(_ColorDirectorTestBase):
    """Tests for populating presets with initial data."""

    def test_populate_short_creates_linear_presets(self):
        """The short initial data consists of linear presets with the default fade in time."""
        director = self._make_director()
        director.populate_presets_with_initial_data(short=True)
        self.assertGreater(len(director.presets), 0)
        three_second_fade = (1000 // STEP_DURATION_MS) * 3
        for preset in director.presets:
            for duration, transfer_function, _ in preset.colors:
                self.assertEqual(duration, three_second_fade)
                self.assertIs(transfer_function, TransferFunction.LINEAR)

    def test_populated_presets_survive_serialization(self):
        """The populated presets survive a serialization round trip."""
        director = self._make_director()
        director.populate_presets_with_initial_data(short=False)
        director.serialize()
        preset_configuration = director.filter_configurations["presets"]

        reparsed = self._make_director(presets=preset_configuration)
        reparsed.serialize()
        self.assertEqual(reparsed.filter_configurations["presets"], preset_configuration)
        self.assertEqual(len(reparsed.presets), len(director.presets))


class ModelMutationTest(_ColorDirectorTestBase):
    """Tests for the model methods modifying presets, recalls and color groups."""

    def test_presets_property_returns_copy(self):
        """The presets property returns a copy: Structural changes of it do not affect the filter."""
        director = self._make_director()
        presets = director.presets
        presets.append(ColorPreset())
        self.assertEqual(director.presets, [])

    def test_add_and_remove_preset(self):
        """add_preset appends presets and remove_preset removes known presets only."""
        director = self._make_director()
        preset = ColorPreset()
        director.add_preset(preset)
        self.assertEqual(director.presets, [preset])
        self.assertTrue(director.remove_preset(preset))
        self.assertEqual(director.presets, [])
        self.assertFalse(director.remove_preset(preset))

    def test_recalls_property_returns_copy(self):
        """The recalls property returns a copy: Structural changes of it do not affect the filter."""
        director = self._make_director(color_groups="g|a", recalls="0")
        recalls = director.recalls
        recalls.pop(0)
        self.assertEqual(director.recalls, [[0]])

    def test_add_and_remove_recall(self):
        """add_recall creates a recall with an entry per color group, remove_recall ignores unknown indices."""
        director = self._make_director(color_groups="g|a#b|c")
        recall = director.add_recall()
        self.assertEqual(recall, [0, 0])
        self.assertEqual(director.recalls, [[0, 0]])
        director.remove_recall(0)
        self.assertEqual(director.recalls, [])
        director.remove_recall(0)

    def test_set_recall_preset_normalizes_and_bounds(self):
        """set_recall_preset normalizes the recall and bounds the stored preset index."""
        director = self._make_director(color_groups="g|a#b|c", presets="12|lin|120.0,0.5,0.75$12|lin|10.0,0.5,0.5")
        recall = director.add_recall()
        self.assertTrue(director.set_recall_preset(0, 1, 1))
        self.assertEqual(recall, [0, 1])
        self.assertTrue(director.set_recall_preset(0, 1, 5))
        self.assertEqual(recall, [0, 0])
        self.assertFalse(director.set_recall_preset(0, -1, 0))
        self.assertFalse(director.set_recall_preset(0, 2, 0))
        self.assertFalse(director.set_recall_preset(1, 0, 0))

    def test_output_groups_property_returns_copy(self):
        """The output_groups property returns a copy: Changes of its structure do not affect the filter."""
        director = self._make_director(color_groups="g|a")
        groups = director.output_groups
        groups["new"] = []
        del groups["g"]
        self.assertEqual(director.output_groups, {"g": ["a"]})

    def test_add_output_group_and_sub_output(self):
        """add_output_group and add_sub_output validate their names within the model."""
        director = self._make_director(color_groups="g|a")
        self.assertFalse(director.add_output_group("g"))
        self.assertFalse(director.add_output_group("a__b"))
        self.assertTrue(director.add_output_group("h"))
        self.assertEqual(director.output_groups, {"g": ["a"], "h": []})
        self.assertFalse(director.add_sub_output("g", "a"))
        self.assertFalse(director.add_sub_output("g", "a__b"))
        self.assertFalse(director.add_sub_output("bogus", "x"))
        self.assertTrue(director.add_sub_output("g", "b"))
        self.assertEqual(director.output_groups, {"g": ["a", "b"], "h": []})
        self.assertEqual(director.get_outputs(), ["g__a", "g__b"])

    def test_remove_sub_output(self):
        """remove_sub_output removes known sub outputs only."""
        director = self._make_director(color_groups="g|a#b|c")
        self.assertFalse(director.remove_sub_output("bogus", "a"))
        self.assertFalse(director.remove_sub_output("g", "x"))
        self.assertTrue(director.remove_sub_output("g", "a"))
        self.assertEqual(director.output_groups, {"g": [], "b": ["c"]})

    def test_get_current_active_colors_returns_copy(self):
        """get_current_active_colors returns a copy that may be modified without affecting the filter."""
        director = self._make_director(color_groups="g|a", presets="12|lin|120.0,0.5,0.75")
        director._cue_filter_to_group_index_mapping["colordirector__cue__g"] = 0
        director._update_active_colors_from_filters(_FakeFilterUpdateMessage("colordirector__cue__g", "run;0"))
        active_colors = director.get_current_active_colors()
        self.assertEqual(active_colors, [0])
        self.assertIsNot(active_colors, director.get_current_active_colors())
        active_colors.clear()
        self.assertEqual(director.get_current_active_colors(), [0])
