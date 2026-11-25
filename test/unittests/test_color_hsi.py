"""Unit tests for the ColorHSI model.

Also guards the regression where a stale HLS variant of ``from_rgb`` silently
overrode the HSV-based one (see git commits 43514c1d, 890ff63b, 3145d098).
"""

import colorsys
import unittest

from model.color_hsi import ColorHSI


class ColorHSIConversionTest(unittest.TestCase):
    """Conversion round-trips and HSV-vs-HLS guards for the ColorHSI model."""

    def test_from_rgb_to_rgb_round_trip(self) -> None:
        """RGB int → ColorHSI → RGB int must round-trip within one LSB per channel."""
        for r, g, b in [(255, 128, 32), (0, 0, 0), (255, 255, 255), (1, 2, 3), (240, 17, 99)]:
            c = ColorHSI.from_rgb(r, g, b)
            rr, gg, bb = c.to_rgb()
            self.assertLessEqual(abs(rr - r), 1)
            self.assertLessEqual(abs(gg - g), 1)
            self.assertLessEqual(abs(bb - b), 1)

    def test_from_rgb_float_round_trip(self) -> None:
        """RGB float → ColorHSI → RGB float must round-trip to 1e-6."""
        for r, g, b in [(0.2, 0.5, 0.9), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.123, 0.456, 0.789)]:
            c = ColorHSI.from_rgb_float(r, g, b)
            rr, gg, bb = c.to_rgb_float()
            self.assertAlmostEqual(rr, r, places=6)
            self.assertAlmostEqual(gg, g, places=6)
            self.assertAlmostEqual(bb, b, places=6)

    def test_from_rgb_int_and_float_agree(self) -> None:
        """Regression: the HLS-override of ``from_rgb`` used to make these disagree."""
        for r, g, b in [(100, 150, 200), (255, 0, 0), (0, 255, 0), (12, 34, 56)]:
            c_int = ColorHSI.from_rgb(r, g, b)
            c_float = ColorHSI.from_rgb_float(r / 255, g / 255, b / 255)
            self.assertEqual(c_int, c_float)

    def test_from_rgb_uses_hsv_not_hls(self) -> None:
        """Explicit HSV check: hue of pure red must be 0, saturation 1, value 1."""
        c = ColorHSI.from_rgb(255, 0, 0)
        self.assertAlmostEqual(c.hue, 0.0, places=6)
        self.assertAlmostEqual(c.saturation, 1.0, places=6)
        self.assertAlmostEqual(c.intensity, 1.0, places=6)
        # Compare against colorsys HSV directly to fail loudly if someone re-adds an HLS variant.
        h, s, v = colorsys.rgb_to_hsv(1.0, 0.0, 0.0)
        self.assertAlmostEqual(c.hue, h * 360.0, places=6)
        self.assertAlmostEqual(c.saturation, s, places=6)
        self.assertAlmostEqual(c.intensity, v, places=6)

    def test_from_cmy(self) -> None:
        """CMY=(0,0,1) must be yellow, same as RGB=(255,255,0)."""
        c_cmy = ColorHSI.from_cmy(0.0, 0.0, 1.0)
        c_rgb = ColorHSI.from_rgb(255, 255, 0)
        self.assertEqual(c_cmy, c_rgb)

    def test_to_cmy_round_trip(self) -> None:
        """ColorHSI → CMY → ColorHSI must round-trip identically."""
        for h, s, v in [(0.0, 1.0, 1.0), (120.0, 0.8, 0.6), (240.0, 0.4, 0.9)]:
            original = ColorHSI(h, s, v)
            c, m, y = original.to_cmy()
            restored = ColorHSI.from_cmy(c, m, y)
            self.assertEqual(original, restored)

    def test_to_rgb_rounds_symmetrically(self) -> None:
        """Previously ``int()`` truncation biased values low (e.g. 127.6 → 127)."""
        c = ColorHSI.from_rgb(128, 64, 200)
        r, g, b = c.to_rgb()
        self.assertEqual((r, g, b), (128, 64, 200))

    def test_equality(self) -> None:
        """Equal colors compare equal and hash equal; different ones compare unequal."""
        a = ColorHSI(120.0, 0.5, 0.5)
        b = ColorHSI(120.0, 0.5, 0.5)
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        c = ColorHSI(120.0, 0.5, 0.6)
        self.assertNotEqual(a, c)

    def test_equality_within_tolerance(self) -> None:
        """Colors differing by less than the HSV tolerance must still compare equal."""
        a = ColorHSI(120.0, 0.5, 0.5)
        b = ColorHSI(120.0 + 1e-8, 0.5, 0.5 - 1e-8)
        self.assertEqual(a, b)

    def test_equality_with_non_coloract(self) -> None:
        """Comparing a ColorHSI to a non-ColorHSI must yield NotImplemented (false)."""
        a = ColorHSI(0.0, 0.0, 0.0)
        self.assertNotEqual(a, "not a color")
        self.assertNotEqual(a, 0)

    def test_hex_round_trip(self) -> None:
        """Round-trip through the HTML hex representation that ``color_name_dict`` uses."""
        c = ColorHSI.from_rgb(255, 128, 64)
        hex_str = str(c)
        self.assertEqual(hex_str, "#FF8040")
        # Simulated parse (same as color_name_dict.py:31-36)
        r = int(hex_str[1:3], 16)
        g = int(hex_str[3:5], 16)
        b = int(hex_str[5:7], 16)
        restored = ColorHSI.from_rgb(r, g, b)
        self.assertEqual(c, restored)


class ColorHSIClampingTest(unittest.TestCase):
    """Boundary / clamping behavior for the ColorHSI constructor and from-RGB helpers."""

    def test_hue_modulo(self) -> None:
        """Hue values outside [0, 360) must wrap via modulo."""
        c = ColorHSI(720.0 + 45.0, 0.5, 0.5)
        self.assertAlmostEqual(c.hue, 45.0, places=6)

    def test_saturation_clamped(self) -> None:
        """Out-of-range saturation values must clamp to [0, 1]."""
        self.assertAlmostEqual(ColorHSI(0.0, -0.3, 0.5).saturation, 0.0)
        self.assertAlmostEqual(ColorHSI(0.0, 1.7, 0.5).saturation, 1.0)

    def test_intensity_clamped(self) -> None:
        """Out-of-range intensity values must clamp to [0, 1]."""
        self.assertAlmostEqual(ColorHSI(0.0, 0.5, -0.1).intensity, 0.0)
        self.assertAlmostEqual(ColorHSI(0.0, 0.5, 2.0).intensity, 1.0)

    def test_from_rgb_float_clamped(self) -> None:
        """RGB floats outside [0, 1] must clamp before HSV conversion."""
        c = ColorHSI.from_rgb_float(-0.5, 2.0, 0.5)
        # Clamped input is equivalent to from_rgb_float(0, 1, 0.5).
        expected = ColorHSI.from_rgb_float(0.0, 1.0, 0.5)
        self.assertEqual(c, expected)


if __name__ == "__main__":
    unittest.main()
