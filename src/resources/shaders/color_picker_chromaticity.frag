#version 410 core

// CIE 1931 xy chromaticity diagram renderer.
// - Fills pixels inside the spectral-locus horseshoe with the sRGB color
//   equivalent to the fragment's xy at the currently-selected luminance.
// - Pixels outside the sRGB gamut triangle are dimmed to a desaturated tone.
// - Pixels outside the spectral-locus polygon are painted with uBackground.
// - Overlays spectral-locus outline, sRGB gamut triangle, and a crosshair at
//   uCursorXY.

in vec2 vXY;
layout(location = 0) out vec4 outColor;

const int MAX_LOCUS = 96;

uniform float uY;
uniform vec2  uCursorXY;
uniform float uPixelPerXYUnit;
uniform vec3  uBackground;

uniform int   uLocusCount;
uniform vec2  uLocus[MAX_LOCUS];
uniform vec2  uGamut[3];
uniform vec2  uDomain;

// XYZ (D65) -> linear sRGB (D65), IEC 61966-2-1.  Column vectors.
const mat3 M_XYZ_TO_LRGB = mat3(
     3.2406, -0.9689,  0.0557,   // column 0 (multiplied by X)
    -1.5372,  1.8758, -0.2040,   // column 1 (Y)
    -0.4986,  0.0415,  1.0570    // column 2 (Z)
);

float srgb_oetf(float c) {
    return c <= 0.0031308 ? 12.92 * c : 1.055 * pow(c, 1.0 / 2.4) - 0.055;
}

vec3 srgb_oetf_vec(vec3 c) {
    return vec3(srgb_oetf(c.r), srgb_oetf(c.g), srgb_oetf(c.b));
}

// Point in polygon (even-odd rule).
bool point_in_locus(vec2 p) {
    bool inside = false;
    int n = uLocusCount;
    for (int i = 0, j = n - 1; i < n; j = i, ++i) {
        vec2 vi = uLocus[i];
        vec2 vj = uLocus[j];
        if (((vi.y > p.y) != (vj.y > p.y))
            && (p.x < (vj.x - vi.x) * (p.y - vi.y) / (vj.y - vi.y + 1e-30) + vi.x)) {
            inside = !inside;
        }
    }
    return inside;
}

float point_to_segment(vec2 p, vec2 a, vec2 b) {
    vec2 ab = b - a;
    float l2 = max(dot(ab, ab), 1e-30);
    float t = clamp(dot(p - a, ab) / l2, 0.0, 1.0);
    vec2 c = a + t * ab;
    return length(p - c);
}

float distance_to_locus(vec2 p) {
    float best = 1e30;
    int n = uLocusCount;
    for (int i = 0; i < n; ++i) {
        vec2 a = uLocus[i];
        // Wrap around to index 0 instead of wrapping into stale slots past uLocusCount.
        int j = (i + 1 < n) ? (i + 1) : 0;
        vec2 b = uLocus[j];
        best = min(best, point_to_segment(p, a, b));
    }
    return best;
}

float distance_to_gamut_triangle(vec2 p) {
    float d0 = point_to_segment(p, uGamut[0], uGamut[1]);
    float d1 = point_to_segment(p, uGamut[1], uGamut[2]);
    float d2 = point_to_segment(p, uGamut[2], uGamut[0]);
    return min(d0, min(d1, d2));
}

bool point_in_triangle(vec2 p, vec2 a, vec2 b, vec2 c) {
    // Sign of cross products.
    float s1 = (p.x - b.x) * (a.y - b.y) - (a.x - b.x) * (p.y - b.y);
    float s2 = (p.x - c.x) * (b.y - c.y) - (b.x - c.x) * (p.y - c.y);
    float s3 = (p.x - a.x) * (c.y - a.y) - (c.x - a.x) * (p.y - a.y);
    bool has_neg = (s1 < 0.0) || (s2 < 0.0) || (s3 < 0.0);
    bool has_pos = (s1 > 0.0) || (s2 > 0.0) || (s3 > 0.0);
    return !(has_neg && has_pos);
}

void main() {
    vec2 xy = vXY * uDomain;

    if (!point_in_locus(xy)) {
        outColor = vec4(uBackground, 1.0);
        return;
    }

    // Project xy onto a unit-luminance XYZ, then into linear sRGB.  We
    // normalize to the pure-hue representation (max channel = 1) so the
    // displayed color is modulated purely by the HSV V uniform.  This keeps
    // the diagram looking uniformly bright at any intensity (otherwise
    // in-gamut pixels pick up natural CIE luminance scaling while out-of-gamut
    // pixels get dimmed, which yields the "bright triangle, dim horseshoe"
    // artifact at intermediate V values).
    //
    // Invariant: point_in_locus(xy) has already returned true, so xy lies
    // inside the spectral horseshoe.  That guarantees xy.y > 0 (the horseshoe
    // never touches the x-axis) and x + y <= 1 within the locus, so
    // (1 - xy.x - xy.y) >= 0 and the z component below is non-negative.  The
    // y_safe clamp is only belt-and-braces for fragments at the extreme
    // bottom edge of the mapping.
    float y_safe = max(xy.y, 1e-4);
    vec3 XYZ_unit = vec3(xy.x / y_safe, 1.0, (1.0 - xy.x - xy.y) / y_safe);
    vec3 linear_rgb = M_XYZ_TO_LRGB * XYZ_unit;

    // OOG = any negative component (xy outside sRGB triangle).
    bool oog = any(lessThan(linear_rgb, vec3(0.0)));

    // Clamp negatives (project OOG onto the gamut boundary).
    linear_rgb = max(linear_rgb, vec3(0.0));

    // Normalize: max channel = 1 → fully saturated hue at this chromaticity.
    float max_ch = max(linear_rgb.r, max(linear_rgb.g, linear_rgb.b));
    linear_rgb /= max(max_ch, 1e-6);

    // Apply OETF, then dim by intensity as a straight sRGB multiplier (HSV V semantics).
    vec3 srgb = srgb_oetf_vec(linear_rgb) * uY;

    if (oog) {
        // Dim + desaturate to indicate "unreachable on sRGB".
        float gray = dot(srgb, vec3(0.2126, 0.7152, 0.0722));
        srgb = mix(vec3(gray), srgb, 0.4) * 0.6;
    }

    // Overlay: spectral-locus outline (black with 1px AA).
    float d_locus = distance_to_locus(xy);
    float t_locus = smoothstep(1.5 / uPixelPerXYUnit, 0.5 / uPixelPerXYUnit, d_locus);
    srgb = mix(srgb, vec3(0.0), t_locus);

    // Overlay: sRGB gamut triangle outline (soft white).
    float d_gamut = distance_to_gamut_triangle(xy);
    float t_gamut = smoothstep(1.5 / uPixelPerXYUnit, 0.5 / uPixelPerXYUnit, d_gamut);
    srgb = mix(srgb, vec3(1.0), t_gamut * 0.6);

    // Overlay: crosshair at uCursorXY.  Draw a short cross with black outline
    // and white inner so it is readable on any underlying color.
    vec2 dcursor = (xy - uCursorXY) * uPixelPerXYUnit;
    float arm = 10.0;
    float thick_outer = 3.0;
    float thick_inner = 1.0;
    bool on_arm = (abs(dcursor.x) <= arm && abs(dcursor.y) <= thick_outer) ||
                  (abs(dcursor.y) <= arm && abs(dcursor.x) <= thick_outer);
    bool on_inner = (abs(dcursor.x) <= arm - 1.0 && abs(dcursor.y) <= thick_inner) ||
                    (abs(dcursor.y) <= arm - 1.0 && abs(dcursor.x) <= thick_inner);
    if (on_arm) {
        srgb = on_inner ? vec3(1.0) : vec3(0.0);
    }

    outColor = vec4(srgb, 1.0);
}
