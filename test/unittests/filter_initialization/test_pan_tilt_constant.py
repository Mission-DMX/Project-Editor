"""Tests for the pan/tilt constant filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class PanTiltConstantFilterTests(unittest.TestCase):
    """Per-type assertions for PanTiltConstantFilter migrated in PR 17."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_16bit_outputs_and_center_pan_tilt(self) -> None:
        """Default PanTiltConstant has 16-bit pan/tilt outputs centered at 0.5."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_POSITION_CONSTANT, filter_id="pt"
        )
        self.assertEqual(f.filter_configurations["outputs"], "16bit")
        self.assertEqual(f.initial_parameters["pan"], "0.5")
        self.assertEqual(f.initial_parameters["tilt"], "0.5")
        self.assertEqual(
            f.out_data_types,
            {"pan16bit": DataType.DT_16_BIT, "tilt16bit": DataType.DT_16_BIT},
        )
        self.assertEqual(f.gui_update_keys.get("pan"), DataType.DT_DOUBLE)

    def test_outputs_eight_bit(self) -> None:
        """``outputs=8bit`` exposes only the 8-bit pan/tilt output ports."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_POSITION_CONSTANT,
            filter_id="pt",
            filter_configurations={"outputs": "8bit"},
        )
        self.assertEqual(
            f.out_data_types,
            {"pan8bit": DataType.DT_8_BIT, "tilt8bit": DataType.DT_8_BIT},
        )

    def test_outputs_both_exposes_all_four(self) -> None:
        """``outputs=both`` exposes both 8bit and 16bit pan/tilt output ports."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_POSITION_CONSTANT,
            filter_id="pt",
            filter_configurations={"outputs": "both"},
        )
        self.assertEqual(set(f.out_data_types.keys()), {"pan16bit", "tilt16bit", "pan8bit", "tilt8bit"})
        self.assertEqual(f.out_data_types["pan16bit"], DataType.DT_16_BIT)
        self.assertEqual(f.out_data_types["pan8bit"], DataType.DT_8_BIT)

    def test_outputs_switch_rebuilds_on_update_filter_configuration(self) -> None:
        """Switching the ``outputs`` config via ``update_filter_configuration`` rebuilds the ports."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_POSITION_CONSTANT, filter_id="pt"
        )
        self.assertEqual(set(f.out_data_types.keys()), {"pan16bit", "tilt16bit"})
        f.update_filter_configuration("outputs", "both")
        self.assertEqual(set(f.out_data_types.keys()), {"pan16bit", "tilt16bit", "pan8bit", "tilt8bit"})
        f.update_filter_configuration("outputs", "8bit")
        self.assertEqual(set(f.out_data_types.keys()), {"pan8bit", "tilt8bit"})

    def test_loaded_initial_parameters_override_defaults(self) -> None:
        """Loaded pan/tilt values must take precedence over the center defaults."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_POSITION_CONSTANT,
            filter_id="pt",
            initial_parameters={"pan": "0.25", "tilt": "0.75"},
        )
        self.assertEqual(f.initial_parameters["pan"], "0.25")
        self.assertEqual(f.initial_parameters["tilt"], "0.75")
