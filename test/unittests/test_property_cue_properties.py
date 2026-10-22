"""Unit tests for property-based cue properties and distribution (WP4)."""

from __future__ import annotations

import math
import unittest
from logging import getLogger

from model.color_hsi import ColorHSI
from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.distribution import Distribution, DistributionMethod
from model.virtual_filters.property_cues.properties import (
    CURVE_SIN,
    BeamProperty,
    ColourProperty,
    DimmerProperty,
    FrostProperty,
    GoboProperty,
    PositionProperty,
    seconds_to_timesteps,
)

logger = getLogger(__name__)


_CONSTANT = Distribution(method=DistributionMethod.CONSTANT)


class DistributionTest(unittest.TestCase):

    def test_constant_zero_delay(self) -> None:
        dist = Distribution(method=DistributionMethod.CONSTANT, phase_offset=99.0, amplitude=12.0)
        for idx in range(5):
            self.assertEqual(0.0, dist.delay_for_child(idx))

    def test_phase_linear_sequence(self) -> None:
        dist = Distribution(method=DistributionMethod.PHASE_LINEAR, phase_offset=0.5, amplitude=1.0)
        delays = [dist.delay_for_child(i) for i in range(4)]
        self.assertEqual([0.0, 0.5, 1.0, 1.5], delays)

    def test_phase_sin_amplitude(self) -> None:
        dist = Distribution(method=DistributionMethod.PHASE_SIN, phase_offset=math.pi / 2, amplitude=2.0)
        delays = [dist.delay_for_child(i) for i in range(4)]
        self.assertAlmostEqual(0.0, delays[0], places=6)
        self.assertAlmostEqual(2.0, delays[1], places=6)
        self.assertAlmostEqual(0.0, delays[2], places=6)
        self.assertAlmostEqual(-2.0, delays[3], places=6)

    def test_phase_cos_amplitude(self) -> None:
        dist = Distribution(method=DistributionMethod.PHASE_COS, phase_offset=math.pi, amplitude=1.0)
        delays = [dist.delay_for_child(i) for i in range(3)]
        self.assertAlmostEqual(1.0, delays[0], places=6)
        self.assertAlmostEqual(-1.0, delays[1], places=6)
        self.assertAlmostEqual(1.0, delays[2], places=6)

    def test_phase_saw_shape(self) -> None:
        dist = Distribution(method=DistributionMethod.PHASE_SAW, phase_offset=math.pi, amplitude=1.0)
        # phase_offset=pi -> fraction increments by 0.5 per step.
        # child 0 -> fraction 0.0  -> (0.0 - 0.5)*2 = -1.0
        # child 1 -> fraction 0.5  -> (0.5 - 0.5)*2 =  0.0
        # child 2 -> fraction 0.0  -> (0.0 - 0.5)*2 = -1.0
        delays = [dist.delay_for_child(i) for i in range(3)]
        self.assertAlmostEqual(-1.0, delays[0], places=6)
        self.assertAlmostEqual(0.0, delays[1], places=6)
        self.assertAlmostEqual(-1.0, delays[2], places=6)


class DimmerPropertyTest(unittest.TestCase):

    def test_channel_specs(self) -> None:
        specs = DimmerProperty().channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {"brightness": DataType.DT_DOUBLE, "strobefreq": DataType.DT_DOUBLE, "duty_cycle": DataType.DT_DOUBLE},
            names_to_types,
        )

    def test_single_request_at_step_start(self) -> None:
        prop = DimmerProperty(
            brightness=0.75, strobefreq=0.0, duty_cycle=200.0, transition=TransferFunction.LINEAR,
        )
        reqs = prop.generate_requests(step_start_40hz=100, step_duration_40hz=400, child_index=0, distribution=_CONSTANT)
        self.assertIn("brightness", reqs)
        self.assertEqual(1, len(reqs["brightness"]))
        req = reqs["brightness"][0]
        self.assertEqual(100, req.timestep_40hz)
        self.assertEqual(0.75, req.requested_value)
        self.assertIs(TransferFunction.LINEAR, req.transition)
        strobe_req = reqs["strobefreq"][0]
        self.assertEqual(100, strobe_req.timestep_40hz)
        self.assertEqual(0.0, strobe_req.requested_value)
        duty_req = reqs["duty_cycle"][0]
        self.assertEqual(100, duty_req.timestep_40hz)
        self.assertEqual(200.0, duty_req.requested_value)
        self.assertIs(TransferFunction.LINEAR, duty_req.transition)

    def test_default_duty_cycle_is_balanced(self) -> None:
        reqs = DimmerProperty().generate_requests(
            step_start_40hz=0, step_duration_40hz=40, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual(128.0, reqs["duty_cycle"][0].requested_value)

    def test_phase_linear_delays_children(self) -> None:
        prop = DimmerProperty(brightness=1.0)
        dist = Distribution(method=DistributionMethod.PHASE_LINEAR, phase_offset=0.5, amplitude=1.0)
        starts: list[int] = []
        for child in range(4):
            reqs = prop.generate_requests(
                step_start_40hz=0, step_duration_40hz=400, child_index=child, distribution=dist,
            )
            starts.append(reqs["brightness"][0].timestep_40hz)
        expected = [seconds_to_timesteps(0.5 * i) for i in range(4)]
        self.assertEqual(expected, starts)
        self.assertEqual([0, 20, 40, 60], starts)


class PositionPropertyTest(unittest.TestCase):

    def test_channel_specs(self) -> None:
        specs = PositionProperty().channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {
                "pan_value": DataType.DT_DOUBLE,
                "pan_curvesel": DataType.DT_8_BIT,
                "tilt_value": DataType.DT_DOUBLE,
                "tilt_curvesel": DataType.DT_8_BIT,
            },
            names_to_types,
        )

    def test_curvesel_constant_across_children(self) -> None:
        prop = PositionProperty(pan_value=0.5, pan_curvesel=CURVE_SIN, tilt_value=0.25)
        dist = Distribution(method=DistributionMethod.PHASE_LINEAR, phase_offset=0.25, amplitude=1.0)
        for child in range(3):
            reqs = prop.generate_requests(
                step_start_40hz=40, step_duration_40hz=200, child_index=child, distribution=dist,
            )
            self.assertEqual(CURVE_SIN, reqs["pan_curvesel"][0].requested_value)
            # Discrete channel still picks up the delay.
            expected_slot = 40 + seconds_to_timesteps(0.25 * child)
            self.assertEqual(expected_slot, reqs["pan_curvesel"][0].timestep_40hz)
            self.assertEqual(expected_slot, reqs["pan_value"][0].timestep_40hz)


class ColourPropertyTest(unittest.TestCase):

    def test_channel_specs(self) -> None:
        specs = ColourProperty().channel_specs
        self.assertEqual(("color",), tuple(s.name for s in specs))
        self.assertEqual(DataType.DT_COLOR, specs[0].data_type)

    def test_discrete_value_unchanged_across_children(self) -> None:
        colour = ColorHSI(120.0, 1.0, 0.5)
        prop = ColourProperty(color=colour, transition=TransferFunction.EDGE)
        dist = Distribution(method=DistributionMethod.PHASE_SIN, phase_offset=math.pi / 2, amplitude=1.0)
        values: list = []
        slots: list[int] = []
        for child in range(4):
            reqs = prop.generate_requests(
                step_start_40hz=200, step_duration_40hz=200, child_index=child, distribution=dist,
            )
            self.assertEqual(1, len(reqs["color"]))
            values.append(reqs["color"][0].requested_value)
            slots.append(reqs["color"][0].timestep_40hz)
        self.assertTrue(all(v is colour for v in values))
        # Delay is applied to the slot even on discrete channels.
        self.assertNotEqual(slots[0], slots[1])


class GoboPropertyTest(unittest.TestCase):

    def test_channel_specs_single_wheel(self) -> None:
        specs = GoboProperty(wheel_count=1).channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {"goboslot_0": DataType.DT_8_BIT, "goborotation_0": DataType.DT_DOUBLE},
            names_to_types,
        )

    def test_channel_specs_two_wheels(self) -> None:
        specs = GoboProperty(wheel_count=2).channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {
                "goboslot_0": DataType.DT_8_BIT,
                "goborotation_0": DataType.DT_DOUBLE,
                "goboslot_1": DataType.DT_8_BIT,
                "goborotation_1": DataType.DT_DOUBLE,
            },
            names_to_types,
        )

    def test_requests_two_wheels(self) -> None:
        prop = GoboProperty(wheel_count=2, slots={0: 3, 1: 5}, rotations={0: 0.25, 1: -0.5})
        reqs = prop.generate_requests(
            step_start_40hz=10, step_duration_40hz=100, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual({"goboslot_0", "goborotation_0", "goboslot_1", "goborotation_1"}, set(reqs.keys()))
        self.assertEqual(3, reqs["goboslot_0"][0].requested_value)
        self.assertEqual(5, reqs["goboslot_1"][0].requested_value)
        self.assertEqual(0.25, reqs["goborotation_0"][0].requested_value)
        self.assertEqual(-0.5, reqs["goborotation_1"][0].requested_value)


class BeamPropertyTest(unittest.TestCase):

    def test_channel_specs(self) -> None:
        specs = BeamProperty().channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {
                "focus": DataType.DT_8_BIT,
                "zoom": DataType.DT_8_BIT,
                "prism_selection": DataType.DT_8_BIT,
                "prism_rotation": DataType.DT_DOUBLE,
                "iris": DataType.DT_8_BIT,
            },
            names_to_types,
        )

    def test_values_round_trip(self) -> None:
        prop = BeamProperty(focus=12, zoom=200, prism_selection=3, prism_rotation=0.9, iris=42)
        reqs = prop.generate_requests(
            step_start_40hz=0, step_duration_40hz=100, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual(12, reqs["focus"][0].requested_value)
        self.assertEqual(200, reqs["zoom"][0].requested_value)
        self.assertEqual(3, reqs["prism_selection"][0].requested_value)
        self.assertEqual(0.9, reqs["prism_rotation"][0].requested_value)
        self.assertEqual(42, reqs["iris"][0].requested_value)


class FrostPropertyTest(unittest.TestCase):

    def test_channel_specs(self) -> None:
        specs = FrostProperty().channel_specs
        self.assertEqual(("frost_intensity",), tuple(s.name for s in specs))
        self.assertEqual(DataType.DT_8_BIT, specs[0].data_type)

    def test_request_value_type(self) -> None:
        prop = FrostProperty(frost_intensity=128)
        reqs = prop.generate_requests(
            step_start_40hz=5, step_duration_40hz=20, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual(128, reqs["frost_intensity"][0].requested_value)
        self.assertIsInstance(reqs["frost_intensity"][0].requested_value, int)


if __name__ == "__main__":
    unittest.main()
