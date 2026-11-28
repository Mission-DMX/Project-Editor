"""Tests for the cue filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class CueFilterTests(unittest.TestCase):
    """Per-type assertions for the CueFilter v-filter migrated in PR 13.

    The cue v-filter now derives its ``out_data_types`` from ``filter_configurations["mapping"]``
    at construction time, so loaded shows have fully-populated terminals before the editor view
    opens.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_without_mapping(self) -> None:
        """Default CueFilter has time inputs, no outputs, and empty mapping/cuelist configs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(scene=scene, filter_type=FilterTypeEnumeration.VFILTER_CUES, filter_id="c")
        self.assertEqual(
            f.in_data_types,
            {"time": DataType.DT_DOUBLE, "time_scale": DataType.DT_DOUBLE},
        )
        self.assertEqual(f.out_data_types, {})
        self.assertEqual(f.default_values["time_scale"], "1.0")
        self.assertEqual(f.filter_configurations["mapping"], "")
        self.assertEqual(f.filter_configurations["end_handling"], "")
        self.assertEqual(f.filter_configurations["cuelist"], "")
        self.assertEqual(f.gui_update_keys["run_mode"], ["play", "pause", "to_next_cue", "stop"])
        self.assertEqual(f.gui_update_keys["run_cue"], DataType.DT_16_BIT)

    def test_mapping_populates_typed_outputs(self) -> None:
        """A cue ``mapping`` config populates typed outputs for each entry."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_CUES,
            filter_id="c",
            filter_configurations={"mapping": "a:8bit;b:color;c:float;d:16bit"},
        )
        self.assertEqual(
            f.out_data_types,
            {
                "a": DataType.DT_8_BIT,
                "b": DataType.DT_COLOR,
                "c": DataType.DT_DOUBLE,
                "d": DataType.DT_16_BIT,
            },
        )

    def test_malformed_entries_skipped_and_valid_ones_kept(self) -> None:
        """Loader-time robustness: bad mapping entries must be dropped, not raise."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_CUES,
            filter_id="c",
            filter_configurations={"mapping": "good:8bit;nocolonentry;bad:unknown_type;ok:color"},
        )
        self.assertEqual(
            f.out_data_types, {"good": DataType.DT_8_BIT, "ok": DataType.DT_COLOR}
        )

    def test_mapping_change_shrinks_outputs_on_rebuild(self) -> None:
        """Removing entries from ``mapping`` must drop the corresponding outputs after rebuild."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_CUES,
            filter_id="c",
            filter_configurations={"mapping": "a:8bit;b:color"},
        )
        self.assertEqual(set(f.out_data_types.keys()), {"a", "b"})
        f.update_filter_configuration("mapping", "a:8bit")
        self.assertEqual(f.out_data_types, {"a": DataType.DT_8_BIT})
