#version 410 core

in vec2 vUV;          // (0,0) .. (1,1) from the quad
in vec3 vColor;
in float vRadius;
in vec3 vWorldPos;

out vec4 fragColor;

// Optional: if you have a depth buffer you may want to write depth manually
// (the default depth write from gl_FragDepth works fine).

// Parameters you can tweak at runtime
uniform float uGlowFalloff = 2.0;   // higher = sharper edge
uniform vec3  uGlowColor   = vec3(1.0); // colour of the glow (usually same as vColor)
uniform float uGlowIntensity = 1.0; // multiplier for the additive part

void main()
{
    // ---- Compute distance from centre in the disc plane ----
    // vUV goes from (0,0) at lower‑left to (1,1) at upper‑right.
    // Transform to [-0.5, +0.5] and then to radius units.
    vec2 discCoord = (vUV - vec2(0.5)) * 2.0; // now in [-1, +1]
    float dist = length(discCoord) * vRadius; // world distance from centre

    // ---- Discard fragments outside the radius (hard edge) ----
    // If you want a perfectly sharp disc you can just `if (dist > vRadius) discard;`
    // but we keep them and let the smoothstep create a soft edge.
    // The discard is optional; keeping them allows a smoother fall‑off.

    // ---- Compute the radial fall‑off (glow) ----
    // 0 at centre, 1 at radius, >1 outside.
    float t = dist / vRadius;

    // A smoothstep that goes from opaque to transparent a little before the radius.
    // The exponent controls how quickly the glow fades.
    float alpha = 1.0 - smoothstep(0.0, 1.0, pow(t, uGlowFalloff));

    // ---- Final colour ----
    // Base colour (inside the disc) + additive glow that continues past the edge.
    vec3 base = vColor * alpha;                     // inside disc
    vec3 glow = uGlowColor * pow(1.0 - t, 2.0) * uGlowIntensity; // simple radial glow

    // Combine – we keep the alpha of the base disc, but we also output a bright
    // additive component that will be blended later.
    fragColor = vec4(base + glow, alpha);
}