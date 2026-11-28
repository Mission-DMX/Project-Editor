"""Tests for the sequencer filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class SequencerFilterTests(unittest.TestCase):
    """Per-type assertions for SequencerFilter migrated in PR 14."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_without_channels(self) -> None:
        """Default SequencerFilter has time inputs, no outputs, and empty channel/transition configs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(scene=scene, filter_type=FilterTypeEnumeration.VFILTER_SEQUENCER, filter_id="s")
        self.assertEqual(
            f.in_data_types, {"time": DataType.DT_DOUBLE, "time_scale": DataType.DT_DOUBLE}
        )
        self.assertEqual(f.out_data_types, {})
        self.assertEqual(f.default_values["time_scale"], "1.0")
        self.assertEqual(f.filter_configurations["channels"], "")
        self.assertEqual(f.filter_configurations["transitions"], "")

    def test_channels_populate_typed_outputs(self) -> None:
        """Serialised channels in the ``channels`` config populate typed outputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filter_data.sequencer.sequencer_channel import SequencerChannel
        from model.filters.factory import construct_filter_instance

        # Serialise two channels through SequencerChannel so we match the exact format.
        c1 = SequencerChannel("intensity", DataType.DT_8_BIT)
        c2 = SequencerChannel("hue", DataType.DT_COLOR)
        channels_str = f"{c1.format_for_filter()};{c2.format_for_filter()}"

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_SEQUENCER,
            filter_id="s",
            filter_configurations={"channels": channels_str},
        )
        self.assertEqual(set(f.out_data_types.keys()), {"intensity", "hue"})
        self.assertEqual(f.out_data_types["intensity"], DataType.DT_8_BIT)
        self.assertEqual(f.out_data_types["hue"], DataType.DT_COLOR)

    def test_malformed_channel_entry_is_skipped(self) -> None:
        """Malformed sequencer channel entries are dropped without raising."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_SEQUENCER,
            filter_id="s",
            filter_configurations={"channels": "not_a_valid_sequencer_channel_entry"},
        )
        # Degraded gracefully — no outputs added, inputs still present.
        self.assertEqual(f.out_data_types, {})
        self.assertIn("time", f.in_data_types)
