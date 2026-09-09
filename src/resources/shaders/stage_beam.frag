#version 410 core

in vec3 LocalPos;
in vec3 WorldPos;

uniform vec3 beamColor;

// Shadow mapping for volumetric light shafts
uniform mat4 beamLightSpaceMatrix;
uniform sampler2DArray shadowMap;
uniform int beamShadowLayer;
uniform int hasShadow;

// Light source position for ray-marching from light to fragment
uniform vec3 beamLightPos;

out vec4 FragColor;

// Hash function for procedural noise
float hash(vec3 p) {
    p = fract(p * vec3(443.897, 441.423, 437.195));
    p += dot(p, p.yzx + 19.19);
    return fract((p.x + p.y) * p.z);
}

// Smooth 3D value noise
float noise3D(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);  // smoothstep interpolation

    float n = mix(
        mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x),
            mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
        mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x),
            mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y),
        f.z);
    return n;
}

// Multi-octave noise for beam streaks (simulates individual light rays)
float beamNoise(vec3 worldP) {
    float n1 = noise3D(worldP * 0.015);           // large-scale streaks
    float n2 = noise3D(worldP * 0.04) * 0.5;      // medium detail
    float n3 = noise3D(worldP * 0.12) * 0.25;     // fine grain (dust particles)
    float combined = n1 + n2 + n3;
    return 0.4 + 0.6 * combined;  // remap to [0.5, 1.0]
}

// Check shadow map visibility at a world position (single sample)
float sampleShadowAt(vec3 worldP) {
    if (hasShadow == 0) return 1.0;

    vec4 lsPos = beamLightSpaceMatrix * vec4(worldP, 1.0);
    vec3 proj = lsPos.xyz / lsPos.w;
    proj = proj * 0.5 + 0.5;

    if (proj.x < 0.0 || proj.x > 1.0 || proj.y < 0.0 || proj.y > 1.0 || proj.z > 1.0)
        return 1.0;

    float bias = 0.003;
    float curDepth = proj.z;
    float closest = texture(shadowMap, vec3(proj.xy, float(beamShadowLayer))).r;
    return (curDepth - bias > closest) ? 0.0 : 1.0;
}

void main() {
    // Discard fragments below ground plane
    if (WorldPos.y < 0.0) discard;

    float axial = clamp(-LocalPos.z, 0.0, 1.0);
    float coneR = max(axial, 0.001);
    float radial = length(LocalPos.xy) / coneR;

    // Soft gaussian radial falloff
    float edge = exp(-radial * radial * 1.5);
    // Density increases along beam (atmospheric scattering accumulation)
    float density = pow(axial, 0.25);
    // Bright core along center axis (Mie-like forward scattering)
    float core = exp(-radial * radial * 3.5);

    // Ray-march 8 samples from light to fragment for volumetric shadows
    float visibility = 1.0;
    if (hasShadow == 1) {
        vec3 rayDir = WorldPos - beamLightPos;
        float rayLen = length(rayDir);
        if (rayLen > 0.01) {
            float shadow_acc = 0.0;
            const int STEPS = 8;
            for (int s = 0; s < STEPS; s++) {
                float t = (float(s) + 0.5) / float(STEPS);
                vec3 sampleP = beamLightPos + rayDir * t;
                shadow_acc += sampleShadowAt(sampleP);
            }
            visibility = shadow_acc / float(STEPS);
        }
    }

    // Apply streaky noise for atmospheric look
    float streaks = beamNoise(WorldPos);

    // Combine edge, density, core, noise, and shadow visibility
    float alpha = (edge * density * 1.4) + (core * density * 1.8);
    alpha *= streaks;
    alpha *= visibility;
    alpha = clamp(alpha, 0.0, 1.0);

    // Additive blending output
    FragColor = vec4(beamColor * alpha * 6.0, alpha);
}