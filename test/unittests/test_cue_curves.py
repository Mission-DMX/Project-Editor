"""Unit tests for keyframe transition curves."""
import math
import unittest
from logging import getLogger

from model.color_hsi import ColorHSI
from model.filter_data.cues.cue import (
    StateColor,
    StateDouble,
    StateEightBit,
    StateSixteenBit,
)
from model.filter_data.cues.curves import is_compatible, value_at
from model.filter_data.transfer_function import TransferFunction

logger = getLogger(__name__)

_SIGMOIDAL_OFFSET = 0.0024726231566347743340599073722557624510930726498587540880605924
_SIGMOIDAL_SPAN = 1.0 - 2.0 * _SIGMOIDAL_OFFSET


def _expected_sigmoid(t: float) -> float:
    return (1.0 / (1.0 + math.exp(6.0 - t * 12.0)) - _SIGMOIDAL_OFFSET) / _SIGMOIDAL_SPAN


def _make_double(value: float, transition: TransferFunction = TransferFunction.LINEAR) -> StateDouble:
    s = StateDouble(transition.value)
    s._value = value
    return s


def _make_eight(value: int, transition: TransferFunction = TransferFunction.LINEAR) -> StateEightBit:
    s = StateEightBit(transition.value)
    s._value = value
    return s


def _make_sixteen(value: int, transition: TransferFunction = TransferFunction.LINEAR) -> StateSixteenBit:
    s = StateSixteenBit(transition.value)
    s._value = value
    return s


def _make_color(h: float, s: float, i: float, transition: TransferFunction = TransferFunction.LINEAR) -> StateColor:
    sc = StateColor(transition.value)
    sc._value = ColorHSI(h, s, i)
    return sc


class CueCurvesEdgeTest(unittest.TestCase):
    """Validate EDGE transition semantics."""

    def test_edge_returns_prev_until_t_one(self) -> None:
        """Verify EDGE keeps the previous value for all t < 1 and jumps to next at t == 1."""
        prev = _make_double(10.0)
        nxt = _make_double(100.0)
        self.assertEqual(10.0, value_at(0.0, prev, nxt, TransferFunction.EDGE))
        self.assertEqual(10.0, value_at(0.3, prev, nxt, TransferFunction.EDGE))
        self.assertEqual(10.0, value_at(0.999, prev, nxt, TransferFunction.EDGE))
        self.assertEqual(100.0, value_at(1.0, prev, nxt, TransferFunction.EDGE))

    def test_edge_for_eight_bit_rounds_endpoints(self) -> None:
        """Verify EDGE on eight-bit state returns integer endpoints across t range."""
        prev = _make_eight(10)
        nxt = _make_eight(200)
        self.assertEqual(10, value_at(0.0, prev, nxt, TransferFunction.EDGE))
        self.assertEqual(10, value_at(0.9, prev, nxt, TransferFunction.EDGE))
        self.assertEqual(200, value_at(1.0, prev, nxt, TransferFunction.EDGE))


class CueCurvesLinearTest(unittest.TestCase):
    """Validate LINEAR transition semantics."""

    def test_linear_double_half(self) -> None:
        """Verify LINEAR double interpolation at t = 0, 0.5 and 1."""
        prev = _make_double(0.0)
        nxt = _make_double(100.0)
        self.assertAlmostEqual(0.0, value_at(0.0, prev, nxt, TransferFunction.LINEAR))
        self.assertAlmostEqual(50.0, value_at(0.5, prev, nxt, TransferFunction.LINEAR))
        self.assertAlmostEqual(100.0, value_at(1.0, prev, nxt, TransferFunction.LINEAR))

    def test_linear_eight_bit_rounding(self) -> None:
        """Verify LINEAR interpolation rounds to the nearest eight-bit integer."""
        prev = _make_eight(0)
        nxt = _make_eight(255)
        self.assertEqual(0, value_at(0.0, prev, nxt, TransferFunction.LINEAR))
        self.assertEqual(128, value_at(0.5, prev, nxt, TransferFunction.LINEAR))
        self.assertEqual(255, value_at(1.0, prev, nxt, TransferFunction.LINEAR))

    def test_linear_sixteen_bit_rounding(self) -> None:
        """Verify LINEAR interpolation rounds to the nearest sixteen-bit integer."""
        prev = _make_sixteen(0)
        nxt = _make_sixteen(65535)
        self.assertEqual(0, value_at(0.0, prev, nxt, TransferFunction.LINEAR))
        self.assertEqual(round(65535 * 0.5), value_at(0.5, prev, nxt, TransferFunction.LINEAR))
        self.assertEqual(65535, value_at(1.0, prev, nxt, TransferFunction.LINEAR))

    def test_linear_double_quarter(self) -> None:
        """Verify LINEAR interpolation across a signed range at quarter positions."""
        prev = _make_double(-4.0)
        nxt = _make_double(4.0)
        self.assertAlmostEqual(-2.0, value_at(0.25, prev, nxt, TransferFunction.LINEAR))
        self.assertAlmostEqual(2.0, value_at(0.75, prev, nxt, TransferFunction.LINEAR))


class CueCurvesSigmoidalTest(unittest.TestCase):
    """Validate SIGMOIDAL transition semantics."""

    def test_sigmoidal_endpoints(self) -> None:
        """Verify SIGMOIDAL interpolation hits exact endpoint values at t = 0 and t = 1."""
        prev = _make_double(0.0)
        nxt = _make_double(100.0)
        self.assertAlmostEqual(0.0, value_at(0.0, prev, nxt, TransferFunction.SIGMOIDAL))
        self.assertAlmostEqual(100.0, value_at(1.0, prev, nxt, TransferFunction.SIGMOIDAL))

    def test_sigmoidal_half_is_center(self) -> None:
        """Verify SIGMOIDAL at t = 0.5 is centered on the midpoint between endpoints."""
        prev = _make_double(0.0)
        nxt = _make_double(100.0)
        expected = _expected_sigmoid(0.5) * 100.0
        self.assertAlmostEqual(expected, value_at(0.5, prev, nxt, TransferFunction.SIGMOIDAL))
        self.assertAlmostEqual(50.0, value_at(0.5, prev, nxt, TransferFunction.SIGMOIDAL))

    def test_sigmoidal_quarter(self) -> None:
        """Verify SIGMOIDAL interpolation matches the expected sigmoid value at t = 0.25."""
        prev = _make_double(0.0)
        nxt = _make_double(100.0)
        expected = _expected_sigmoid(0.25) * 100.0
        self.assertAlmostEqual(expected, value_at(0.25, prev, nxt, TransferFunction.SIGMOIDAL))


class CueCurvesEaseInTest(unittest.TestCase):
    """Validate EASE_IN transition semantics."""

    def test_ease_in_values(self) -> None:
        """Verify EASE_IN values at t = 0, 0.5 and 1."""
        prev = _make_double(0.0)
        nxt = _make_double(100.0)
        self.assertAlmostEqual(0.0, value_at(0.0, prev, nxt, TransferFunction.EASE_IN))
        self.assertAlmostEqual(25.0, value_at(0.5, prev, nxt, TransferFunction.EASE_IN))
        self.assertAlmostEqual(100.0, value_at(1.0, prev, nxt, TransferFunction.EASE_IN))

    def test_ease_in_quarter(self) -> None:
        """Verify EASE_IN follows the t-squared curve at t = 0.25."""
        prev = _make_double(0.0)
        nxt = _make_double(100.0)
        self.assertAlmostEqual(0.25 * 0.25 * 100.0, value_at(0.25, prev, nxt, TransferFunction.EASE_IN))


class CueCurvesEaseOutTest(unittest.TestCase):
    """Validate EASE_OUT transition semantics."""

    def test_ease_out_values(self) -> None:
        """Verify EASE_OUT values at t = 0, 0.5 and 1."""
        prev = _make_double(0.0)
        nxt = _make_double(100.0)
        self.assertAlmostEqual(0.0, value_at(0.0, prev, nxt, TransferFunction.EASE_OUT))
        self.assertAlmostEqual(75.0, value_at(0.5, prev, nxt, TransferFunction.EASE_OUT))
        self.assertAlmostEqual(100.0, value_at(1.0, prev, nxt, TransferFunction.EASE_OUT))

    def test_ease_out_quarter(self) -> None:
        """Verify EASE_OUT follows the inverse-square curve at t = 0.25."""
        prev = _make_double(0.0)
        nxt = _make_double(100.0)
        expected = (1.0 - (1.0 - 0.25) * (1.0 - 0.25)) * 100.0
        self.assertAlmostEqual(expected, value_at(0.25, prev, nxt, TransferFunction.EASE_OUT))


class CueCurvesColorTest(unittest.TestCase):
    """Validate color interpolation and hue wraparound."""

    def test_color_linear_half(self) -> None:
        """Verify LINEAR color interpolation lerps in RGB at t = 0.5 (F2).

        Fish interpolates colour linearly in RGB, not along the HSI shortest
        hue arc. Going black (0,0,0) → cyan (180,1,1) in HSI corresponds to
        RGB (0,0,0) → (0,255,255); the midpoint RGB (0, 128, 128) converts
        back to HSI ≈ (180, 1, 0.5): cyan hue, full saturation, half
        intensity. Previously this returned (90, 0.5, 0.5), a muted lime
        that fish's realtime engine never produces.
        """
        prev = _make_color(0.0, 0.0, 0.0)
        nxt = _make_color(180.0, 1.0, 1.0)
        result = value_at(0.5, prev, nxt, TransferFunction.LINEAR)
        self.assertIsInstance(result, ColorHSI)
        self.assertAlmostEqual(180.0, result.hue, places=0)
        self.assertAlmostEqual(1.0, result.saturation, places=2)
        self.assertAlmostEqual(0.502, result.intensity, places=2)

    def test_color_endpoints(self) -> None:
        """Verify color interpolation returns the exact endpoint HSI at t = 0 and t = 1."""
        prev = _make_color(10.0, 0.2, 0.3)
        nxt = _make_color(200.0, 0.7, 0.9)
        start = value_at(0.0, prev, nxt, TransferFunction.LINEAR)
        end = value_at(1.0, prev, nxt, TransferFunction.LINEAR)
        self.assertAlmostEqual(10.0, start.hue)
        self.assertAlmostEqual(0.2, start.saturation)
        self.assertAlmostEqual(0.3, start.intensity)
        self.assertAlmostEqual(200.0, end.hue)
        self.assertAlmostEqual(0.7, end.saturation)
        self.assertAlmostEqual(0.9, end.intensity)

    def test_hue_wraparound_short_arc_upward(self) -> None:
        """Verify hue interpolation takes the short arc when crossing 0 upward."""
        prev = _make_color(350.0, 1.0, 1.0)
        nxt = _make_color(10.0, 1.0, 1.0)
        result = value_at(0.5, prev, nxt, TransferFunction.LINEAR)
        hue = result.hue
        hue_dist_to_zero = min(hue, 360.0 - hue)
        self.assertLess(hue_dist_to_zero, 1.0, msg=f"hue {hue} should land near 0/360, not near 180")

    def test_hue_wraparound_short_arc_downward(self) -> None:
        """Verify hue interpolation takes the short arc when crossing 0 downward."""
        prev = _make_color(10.0, 1.0, 1.0)
        nxt = _make_color(350.0, 1.0, 1.0)
        result = value_at(0.5, prev, nxt, TransferFunction.LINEAR)
        hue = result.hue
        hue_dist_to_zero = min(hue, 360.0 - hue)
        self.assertLess(hue_dist_to_zero, 1.0, msg=f"hue {hue} should land near 0/360, not near 180")

    def test_color_edge_transition(self) -> None:
        """Verify EDGE transition on colors holds prev until t = 1 then jumps to next."""
        prev = _make_color(0.0, 0.0, 0.0)
        nxt = _make_color(180.0, 1.0, 1.0)
        before = value_at(0.5, prev, nxt, TransferFunction.EDGE)
        after = value_at(1.0, prev, nxt, TransferFunction.EDGE)
        self.assertAlmostEqual(0.0, before.hue)
        self.assertAlmostEqual(0.0, before.saturation)
        self.assertAlmostEqual(180.0, after.hue)
        self.assertAlmostEqual(1.0, after.saturation)


class CueCurvesCompatibilityTest(unittest.TestCase):
    """Validate ``is_compatible`` detection and fallback behaviour."""

    def test_color_to_numeric_incompatible(self) -> None:
        """Verify color-to-numeric pairs are flagged as incompatible."""
        prev = _make_color(0.0, 0.0, 0.0)
        nxt = _make_double(1.0)
        self.assertFalse(is_compatible(prev, nxt))

    def test_numeric_to_color_incompatible(self) -> None:
        """Verify numeric-to-color pairs are flagged as incompatible."""
        prev = _make_eight(10)
        nxt = _make_color(0.0, 0.0, 0.0)
        self.assertFalse(is_compatible(prev, nxt))

    def test_numeric_variants_compatible(self) -> None:
        """Verify any mix of numeric state widths is treated as compatible."""
        self.assertTrue(is_compatible(_make_eight(0), _make_eight(1)))
        self.assertTrue(is_compatible(_make_eight(0), _make_sixteen(1)))
        self.assertTrue(is_compatible(_make_sixteen(0), _make_double(1.0)))
        self.assertTrue(is_compatible(_make_double(0.0), _make_double(1.0)))

    def test_color_to_color_compatible(self) -> None:
        """Verify color-to-color pairs are treated as compatible."""
        self.assertTrue(is_compatible(_make_color(0.0, 0.0, 0.0), _make_color(180.0, 1.0, 1.0)))

    def test_value_at_raises_on_incompatible(self) -> None:
        """Verify ``value_at`` raises ValueError when endpoints are incompatible."""
        prev = _make_color(0.0, 0.0, 0.0)
        nxt = _make_double(1.0)
        with self.assertRaises(ValueError):
            value_at(0.5, prev, nxt, TransferFunction.LINEAR)


class CueCurvesEqualEndpointsTest(unittest.TestCase):
    """When prev and next hold the same value, every transition returns that value."""

    def test_double_identity(self) -> None:
        """Verify identical double endpoints yield the constant value under every transition."""
        prev = _make_double(42.0)
        nxt = _make_double(42.0)
        for transition in TransferFunction:
            for t in (0.0, 0.25, 0.5, 0.75, 1.0):
                self.assertAlmostEqual(
                    42.0,
                    value_at(t, prev, nxt, transition),
                    msg=f"transition={transition} t={t}",
                )

    def test_eight_bit_identity(self) -> None:
        """Verify identical eight-bit endpoints yield the constant value under every transition."""
        prev = _make_eight(123)
        nxt = _make_eight(123)
        for transition in TransferFunction:
            for t in (0.0, 0.5, 1.0):
                self.assertEqual(
                    123,
                    value_at(t, prev, nxt, transition),
                    msg=f"transition={transition} t={t}",
                )

    def test_color_identity(self) -> None:
        """Verify identical color endpoints yield the constant HSI under every transition."""
        prev = _make_color(72.0, 0.4, 0.8)
        nxt = _make_color(72.0, 0.4, 0.8)
        for transition in TransferFunction:
            for t in (0.0, 0.5, 1.0):
                result = value_at(t, prev, nxt, transition)
                self.assertAlmostEqual(72.0, result.hue)
                self.assertAlmostEqual(0.4, result.saturation)
                self.assertAlmostEqual(0.8, result.intensity)


class CueCurvesClampTest(unittest.TestCase):
    """Numeric clamping behaviour."""

    def test_eight_bit_clamp_above(self) -> None:
        """Verify eight-bit interpolation clamps values above 255 to 255."""
        prev = _make_eight(0)
        nxt = _make_eight(255)
        nxt._value = 500
        self.assertEqual(255, value_at(1.0, prev, nxt, TransferFunction.LINEAR))

    def test_eight_bit_clamp_below(self) -> None:
        """Verify eight-bit interpolation clamps negative values to 0."""
        prev = _make_eight(0)
        nxt = _make_eight(0)
        prev._value = -50
        self.assertEqual(0, value_at(0.0, prev, nxt, TransferFunction.LINEAR))

    def test_double_no_clamp(self) -> None:
        """Verify double interpolation does not clamp beyond the eight-bit range."""
        prev = _make_double(-1000.0)
        nxt = _make_double(2000.0)
        self.assertAlmostEqual(500.0, value_at(0.5, prev, nxt, TransferFunction.LINEAR))


if __name__ == "__main__":
    unittest.main()
