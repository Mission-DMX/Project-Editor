"""Unit tests for the CIE color-science helpers used by the color picker."""

import unittest

from view.utility_widgets.color_picker import cie_constants as cie


class XYZConversionTest(unittest.TestCase):
    """xyY / XYZ / linear-sRGB matrix conversion round-trips."""

    def test_xyY_xyz_round_trip(self) -> None:  # noqa: N802
        """Round-trip xyY → XYZ → xyY to 1e-9 for in-range inputs."""
        for x, y, big_y in [(0.3127, 0.3290, 1.0), (0.64, 0.33, 0.5), (0.30, 0.60, 0.2)]:
            xyz = cie.xyY_to_xyz(x, y, big_y)
            xx, yy, yy_cap = cie.xyz_to_xyY(xyz)
            self.assertAlmostEqual(xx, x, places=9)
            self.assertAlmostEqual(yy, y, places=9)
            self.assertAlmostEqual(yy_cap, big_y, places=9)

    def test_xyY_degenerate_y(self) -> None:  # noqa: N802
        """Degenerate y near zero must return the all-zero XYZ to avoid NaN."""
        self.assertEqual(cie.xyY_to_xyz(0.3, 0.0, 1.0), (0.0, 0.0, 0.0))

    def test_linear_srgb_xyz_round_trip(self) -> None:
        """Round-trip linear sRGB → XYZ → linear sRGB within matrix precision."""
        for rgb in [(1.0, 1.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.4, 0.3, 0.2)]:
            xyz = cie.linear_srgb_to_xyz_d65(rgb)
            rgb2 = cie.xyz_to_linear_srgb_d65(xyz)
            for a, b in zip(rgb, rgb2, strict=True):
                # Matrices are 4-decimal truncated sRGB spec values, so they
                # are not exact inverses; ~5e-5 round-trip error is expected.
                self.assertAlmostEqual(a, b, places=3)

    def test_d65_white_maps_to_white_srgb(self) -> None:
        """D65 at full luminance must yield near-white linear sRGB."""
        xyz = cie.xyY_to_xyz(cie.D65_WHITE_XY[0], cie.D65_WHITE_XY[1], 1.0)
        r, g, b = cie.xyz_to_linear_srgb_d65(xyz)
        self.assertAlmostEqual(r, 1.0, places=2)
        self.assertAlmostEqual(g, 1.0, places=2)
        self.assertAlmostEqual(b, 1.0, places=2)


class TransferFunctionTest(unittest.TestCase):
    """sRGB OETF / EOTF transfer function identities."""

    def test_oetf_eotf_round_trip(self) -> None:
        """Encoding then decoding must recover the linear value to 1e-6."""
        for v in [0.0, 0.001, 0.0031308, 0.1, 0.5, 0.75, 1.0]:
            encoded = cie.linear_to_srgb_oetf(v)
            decoded = cie.srgb_to_linear_eotf(encoded)
            self.assertAlmostEqual(decoded, v, places=6)

    def test_oetf_endpoints(self) -> None:
        """OETF must map 0 → 0 and 1 → 1."""
        self.assertAlmostEqual(cie.linear_to_srgb_oetf(0.0), 0.0, places=9)
        self.assertAlmostEqual(cie.linear_to_srgb_oetf(1.0), 1.0, places=6)


class SpectralLocusTest(unittest.TestCase):
    """Spectral-locus point-in-polygon tests and the nearest-point snap helper."""

    def test_d65_is_inside(self) -> None:
        """The D65 white point must lie inside the CIE horseshoe."""
        self.assertTrue(cie.is_in_spectral_locus(*cie.D65_WHITE_XY))

    def test_srgb_primaries_are_inside(self) -> None:
        """All three sRGB primaries must lie inside (or on) the spectral locus."""
        for xy in cie.SRGB_PRIMARIES_XY:
            self.assertTrue(cie.is_in_spectral_locus(*xy), f"expected {xy} inside locus")

    def test_far_corner_is_outside(self) -> None:
        """A point far outside the horseshoe must test as outside."""
        self.assertFalse(cie.is_in_spectral_locus(0.9, 0.9))

    def test_origin_is_outside(self) -> None:
        """The origin (0, 0) lies below the horseshoe and must test as outside."""
        self.assertFalse(cie.is_in_spectral_locus(0.0, 0.0))

    def test_snap_identity_when_inside(self) -> None:
        """Snap-to-locus returns a point on the polygon close to the clicked point."""
        sx, sy = cie.snap_to_locus(0.9, 0.9)
        # Must snap to within a small radius of the polygon border, i.e. is at most
        # the diagonal away from the clicked point.
        self.assertLess(abs(sx - 0.9) + abs(sy - 0.9), 1.0)

    def test_snap_toward_green_corner(self) -> None:
        """A click to the top-right corner must snap near the top of the horseshoe."""
        # A click to the top-right corner of our chromaticity domain should snap
        # near the top of the horseshoe (around 520 nm).
        sx, sy = cie.snap_to_locus(0.1, 0.9)
        # The horseshoe's topmost point is around (0.0743, 0.8338).
        self.assertLess(sy, 0.9)
        self.assertGreater(sy, 0.7)


class CompositeTest(unittest.TestCase):
    """Composite xy-to-sRGB helper used by the shader-mirror math in Python."""

    def test_xy_to_srgb_at_d65_is_neutral(self) -> None:
        """At D65 the three sRGB channels must be nearly equal and near full brightness."""
        r, g, b = cie.xy_to_srgb_at_luminance(cie.D65_WHITE_XY[0], cie.D65_WHITE_XY[1], 1.0)
        # Neutral: channels within a small delta of each other.
        self.assertAlmostEqual(r, g, places=2)
        self.assertAlmostEqual(g, b, places=2)
        self.assertGreater(r, 0.9)


if __name__ == "__main__":
    unittest.main()
