"""CIE color-science constants and helpers for the chromaticity color picker.

Kept in a Qt- and GL-free module so it can be unit-tested in isolation and
re-used anywhere in the codebase that needs xy / XYZ / sRGB conversions.

Conventions:
    * All chromaticity coordinates (x, y) are in CIE 1931 (2° observer) space.
    * sRGB primaries and the white point are D65.
    * ``linear_sRGB`` means scene-referred linear [0, 1]; ``sRGB`` means the
      gamma-encoded electrical signal values (also [0, 1]) after applying the
      sRGB OETF.
"""

from __future__ import annotations

import math

# CIE 1931 2° observer spectral locus (wavelength → (x, y)) at 5 nm steps
# from 380 nm to 700 nm (65 samples).  Values follow the Wyszecki & Stiles
# tabulation.  The curve is "open" here — closing the polygon back to the
# first point produces the full horseshoe including the purple line.
SPECTRAL_LOCUS_XY: tuple[tuple[float, float], ...] = (
    (0.1741, 0.0050),  # 380 nm
    (0.1740, 0.0050),
    (0.1738, 0.0049),
    (0.1736, 0.0049),
    (0.1733, 0.0048),
    (0.1730, 0.0048),
    (0.1726, 0.0048),
    (0.1721, 0.0048),
    (0.1714, 0.0051),
    (0.1703, 0.0058),
    (0.1689, 0.0069),
    (0.1669, 0.0086),
    (0.1644, 0.0109),
    (0.1611, 0.0138),
    (0.1566, 0.0177),
    (0.1510, 0.0227),
    (0.1440, 0.0297),
    (0.1355, 0.0399),
    (0.1241, 0.0578),
    (0.1096, 0.0868),
    (0.0913, 0.1327),
    (0.0687, 0.2007),
    (0.0454, 0.2950),
    (0.0235, 0.4127),
    (0.0082, 0.5384),
    (0.0039, 0.6548),
    (0.0139, 0.7502),
    (0.0389, 0.8120),
    (0.0743, 0.8338),
    (0.1142, 0.8262),
    (0.1547, 0.8059),
    (0.1929, 0.7816),
    (0.2296, 0.7543),
    (0.2658, 0.7243),
    (0.3016, 0.6923),
    (0.3373, 0.6589),
    (0.3731, 0.6245),
    (0.4087, 0.5896),
    (0.4441, 0.5547),
    (0.4788, 0.5202),
    (0.5125, 0.4866),
    (0.5448, 0.4544),
    (0.5752, 0.4242),
    (0.6029, 0.3965),
    (0.6270, 0.3725),
    (0.6482, 0.3514),
    (0.6658, 0.3340),
    (0.6801, 0.3197),
    (0.6915, 0.3083),
    (0.7006, 0.2993),
    (0.7079, 0.2920),
    (0.7140, 0.2859),
    (0.7190, 0.2809),
    (0.7230, 0.2770),
    (0.7260, 0.2740),
    (0.7283, 0.2717),
    (0.7300, 0.2700),
    (0.7311, 0.2689),
    (0.7320, 0.2680),
    (0.7327, 0.2673),
    (0.7334, 0.2666),
    (0.7340, 0.2660),
    (0.7344, 0.2656),
    (0.7346, 0.2654),
    (0.7347, 0.2653),  # 700 nm
)

# sRGB primaries (D65) in CIE 1931 xy.
SRGB_PRIMARIES_XY: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = (
    (0.6400, 0.3300),  # Red
    (0.3000, 0.6000),  # Green
    (0.1500, 0.0600),  # Blue
)

# D65 white point in CIE 1931 xy.
D65_WHITE_XY: tuple[float, float] = (0.3127, 0.3290)

# Chromaticity domain shown by the diagram: xy in [0, X_MAX] x [0, Y_MAX].
XY_DOMAIN_X: float = 0.8
XY_DOMAIN_Y: float = 0.9

# XYZ (D65) → linear sRGB matrix.  Rows applied to column vector (X, Y, Z).
# Reference: IEC 61966-2-1:1999, sRGB.
XYZ_TO_LINEAR_SRGB_D65: tuple[tuple[float, float, float], ...] = (
    (3.2406, -1.5372, -0.4986),
    (-0.9689, 1.8758, 0.0415),
    (0.0557, -0.2040, 1.0570),
)

# Inverse: linear sRGB → XYZ (D65).
LINEAR_SRGB_TO_XYZ_D65: tuple[tuple[float, float, float], ...] = (
    (0.4124, 0.3576, 0.1805),
    (0.2126, 0.7152, 0.0722),
    (0.0193, 0.1192, 0.9505),
)


def xyY_to_xyz(x: float, y: float, Y: float) -> tuple[float, float, float]:  # noqa: N802,N803
    """Convert CIE xyY to XYZ.

    Degenerate inputs (``y`` near zero, or luminance ``Y`` near zero) collapse
    to the all-zero XYZ.  The companion :func:`xyz_to_xyY` maps this sentinel
    back to the D65 chromaticity with ``Y = 0``, so a degenerate round-trip
    lands on a stable fallback.

    """
    if y < 1e-6 or Y < 1e-12:
        return 0.0, 0.0, 0.0
    big_x = x * Y / y
    big_z = (1.0 - x - y) * Y / y
    return big_x, Y, big_z


def xyz_to_xyY(xyz: tuple[float, float, float]) -> tuple[float, float, float]:  # noqa: N802
    """Convert CIE XYZ to xyY.

    When ``X + Y + Z`` is near zero (the all-zero XYZ emitted by
    :func:`xyY_to_xyz` for degenerate inputs), returns the D65 chromaticity
    with ``Y = 0`` as a stable fallback.
    """
    big_x, big_y, big_z = xyz
    total = big_x + big_y + big_z
    if total < 1e-12:
        return D65_WHITE_XY[0], D65_WHITE_XY[1], 0.0
    return big_x / total, big_y / total, big_y


def xyz_to_linear_srgb_d65(xyz: tuple[float, float, float]) -> tuple[float, float, float]:
    """Convert CIE XYZ (D65) to linear sRGB (D65)."""
    big_x, big_y, big_z = xyz
    m = XYZ_TO_LINEAR_SRGB_D65
    r = m[0][0] * big_x + m[0][1] * big_y + m[0][2] * big_z
    g = m[1][0] * big_x + m[1][1] * big_y + m[1][2] * big_z
    b = m[2][0] * big_x + m[2][1] * big_y + m[2][2] * big_z
    return r, g, b


def linear_srgb_to_xyz_d65(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """Convert linear sRGB (D65) to CIE XYZ (D65)."""
    r, g, b = rgb
    m = LINEAR_SRGB_TO_XYZ_D65
    big_x = m[0][0] * r + m[0][1] * g + m[0][2] * b
    big_y = m[1][0] * r + m[1][1] * g + m[1][2] * b
    big_z = m[2][0] * r + m[2][1] * g + m[2][2] * b
    return big_x, big_y, big_z


def linear_to_srgb_oetf(c: float) -> float:
    """Apply the sRGB opto-electronic transfer function (gamma encode)."""
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def srgb_to_linear_eotf(c: float) -> float:
    """Apply the inverse sRGB OETF (gamma decode) — the display EOTF."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def is_in_spectral_locus(x: float, y: float) -> bool:
    """Point-in-polygon test for the closed CIE horseshoe including the purple line."""
    poly = SPECTRAL_LOCUS_XY
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        # Crossing-number test (also known as even-odd rule).
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi):
            inside = not inside
        j = i
    return inside


def _point_to_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> tuple[float, float, float]:
    """Return (closest_x, closest_y, squared_distance) from P to segment AB."""
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-30:
        return ax, ay, (px - ax) * (px - ax) + (py - ay) * (py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    cx = ax + t * dx
    cy = ay + t * dy
    return cx, cy, (px - cx) * (px - cx) + (py - cy) * (py - cy)


def snap_to_locus(x: float, y: float) -> tuple[float, float]:
    """Return the nearest point on the closed spectral-locus polygon to (x, y)."""
    poly = SPECTRAL_LOCUS_XY
    best_x, best_y, best_d2 = poly[0][0], poly[0][1], math.inf
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        cx, cy, d2 = _point_to_segment(x, y, ax, ay, bx, by)
        if d2 < best_d2:
            best_x, best_y, best_d2 = cx, cy, d2
    return best_x, best_y


def clamp01(c: float) -> float:
    """Clamp a float to the closed interval [0, 1]."""
    return max(0.0, min(c, 1.0))


def linear_srgb_tuple_to_srgb(linear: tuple[float, float, float]) -> tuple[float, float, float]:
    """Vector form of :func:`linear_to_srgb_oetf`, with clamping to [0, 1] before encoding."""
    return (
        linear_to_srgb_oetf(clamp01(linear[0])),
        linear_to_srgb_oetf(clamp01(linear[1])),
        linear_to_srgb_oetf(clamp01(linear[2])),
    )


def xy_to_srgb_at_luminance(x: float, y: float, luminance: float) -> tuple[float, float, float]:
    """Convert CIE xy at the given luminance Y into clamped gamma-encoded sRGB."""
    xyz = xyY_to_xyz(x, y, max(luminance, 1e-6))
    linear = xyz_to_linear_srgb_d65(xyz)
    return linear_srgb_tuple_to_srgb(linear)
