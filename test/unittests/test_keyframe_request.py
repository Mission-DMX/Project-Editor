"""Unit tests for KeyframeRequest and ChannelSpec primitives (WP1)."""

import unittest
from dataclasses import FrozenInstanceError

from model.color_hsi import ColorHSI
from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest


class KeyframeRequestTest(unittest.TestCase):
    """Basic correctness of the KeyframeRequest primitive."""

    def test_default_transition_is_linear(self) -> None:
        req = KeyframeRequest(timestep_40hz=0, requested_value=0.5)
        self.assertEqual(TransferFunction.LINEAR, req.transition)

    def test_frozen(self) -> None:
        req = KeyframeRequest(timestep_40hz=0, requested_value=0.5)
        with self.assertRaises(FrozenInstanceError):
            req.timestep_40hz = 1  # type: ignore[misc]

    def test_slots(self) -> None:
        req = KeyframeRequest(timestep_40hz=0, requested_value=0.5)
        # Slots + frozen rejects unknown attributes; the exact exception type depends on cpython version.
        with self.assertRaises((AttributeError, FrozenInstanceError, TypeError)):
            req.bogus = "x"  # type: ignore[attr-defined]

    def test_equality(self) -> None:
        a = KeyframeRequest(timestep_40hz=1, requested_value=1.0, transition=TransferFunction.EDGE)
        b = KeyframeRequest(timestep_40hz=1, requested_value=1.0, transition=TransferFunction.EDGE)
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_time_ordering(self) -> None:
        a = KeyframeRequest(timestep_40hz=1, requested_value=0.5)
        b = KeyframeRequest(timestep_40hz=2, requested_value=0.5)
        self.assertLess(a, b)
        self.assertEqual([a, b], sorted([b, a]))

    def test_colour_value_allowed(self) -> None:
        c = ColorHSI(120.0, 1.0, 0.5)
        req = KeyframeRequest(timestep_40hz=0, requested_value=c, transition=TransferFunction.SIGMOIDAL)
        self.assertIs(c, req.requested_value)


class ChannelSpecTest(unittest.TestCase):
    """Basic correctness of the ChannelSpec primitive."""

    def test_defaults(self) -> None:
        spec = ChannelSpec(name="MH1__pan_value", data_type=DataType.DT_DOUBLE)
        self.assertEqual("", spec.default_value)
        self.assertEqual((), spec.aliases)

    def test_frozen_and_slots(self) -> None:
        spec = ChannelSpec(name="x", data_type=DataType.DT_8_BIT)
        with self.assertRaises(FrozenInstanceError):
            spec.name = "y"  # type: ignore[misc]

    def test_equality(self) -> None:
        a = ChannelSpec(name="x", data_type=DataType.DT_16_BIT, default_value="42")
        b = ChannelSpec(name="x", data_type=DataType.DT_16_BIT, default_value="42")
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))


if __name__ == "__main__":
    unittest.main()
