#version 410 core

// TODO make MAX_SPOT_LIGHTS a parameter
#define MAX_LIGHTS 16
// TODO make MAX_SHADOW_MAPS a parameter
#define MAX_SHADOWS 4

struct SpotLight {
    vec3 position;
    vec3 direction;
    vec3 color;
    float innerCos;
    float outerCos;
};

uniform int numLights;
uniform SpotLight lights[MAX_LIGHTS];

uniform vec3 viewPos;
uniform vec3 baseColor;
uniform float ambientLevel;

// Selection highlight: 0.0 = normal, >0.0 = glow overlay
uniform float highlightMix;
uniform vec3 highlightColor;

// Shadow mapping
uniform int numShadowLights;
uniform mat4 lightSpaceMatrices[MAX_SHADOWS];
uniform sampler2DArray shadowMap;

in vec3 FragPos;
in vec3 Normal;
out vec4 FragColor;

float calcShadow(int idx) {
    vec4 lsPos = lightSpaceMatrices[idx] * vec4(FragPos, 1.0);
    vec3 proj = lsPos.xyz / lsPos.w;
    proj = proj * 0.5 + 0.5;

    // Outside shadow map = fully lit
    if (proj.x < 0.0 || proj.x > 1.0 || proj.y < 0.0 || proj.y > 1.0 || proj.z > 1.0)
        return 1.0;

    // Slope-based bias to reduce shadow acne on angled surfaces
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lights[idx].position - FragPos);
    float slopeFactor = 1.0 - max(dot(norm, lightDir), 0.0);
    float bias = 0.0008 + 0.002 * slopeFactor;

    float curDepth = proj.z;

    // 3x3 PCF kernel for soft shadow edges
    float lit = 0.0;
    vec2 texelSize = 1.0 / vec2(textureSize(shadowMap, 0).xy);
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            float closest = texture(shadowMap, vec3(proj.xy + vec2(x, y) * texelSize, float(idx))).r;
            lit += (curDepth - bias > closest) ? 0.0 : 1.0;
        }
    }
    return lit / 9.0;
}

void main() {
    vec3 norm = normalize(Normal);
    vec3 result = baseColor * ambientLevel;

    // Subtle fill light from above so geometry is never fully black
    vec3 fillDir = normalize(vec3(0.2, 1.0, 0.1));
    float fillDiff = max(dot(norm, fillDir), 0.0);
    result += baseColor * fillDiff * 0.08;

    for (int i = 0; i < numLights && i < MAX_LIGHTS; i++) {
        vec3 toLight = lights[i].position - FragPos;
        float dist = length(toLight);
        vec3 lightDir = toLight / max(dist, 0.001);

        // Spotlight cone attenuation
        float theta = dot(lightDir, -lights[i].direction);
        float eps = lights[i].innerCos - lights[i].outerCos;
        float spot = clamp((theta - lights[i].outerCos) / max(eps, 0.001), 0.0, 1.0);

        if (spot > 0.0) {
            float diff = max(dot(norm, lightDir), 0.0);
            vec3 viewDir = normalize(viewPos - FragPos);
            vec3 halfDir = normalize(lightDir + viewDir);
            float spec = pow(max(dot(norm, halfDir), 0.0), 64.0);

            // Distance attenuation (quadratic falloff)
            float atten = 1.0 / (1.0 + 0.002 * dist + 0.00003 * dist * dist);

            // Shadow factor
            float shadow = 1.0;
            if (i < numShadowLights) {
                shadow = calcShadow(i);
            }

            vec3 contrib = (diff * baseColor + spec * vec3(0.35)) * lights[i].color;
            result += contrib * spot * atten * shadow * 2.2;
        }
    }

    // Reinhard tone mapping
    result = result / (result + vec3(1.0));

    // Selection highlight overlay (neon-yellow for single, orange for multi)
    if (highlightMix > 0.0) {
        result = mix(result, highlightColor, highlightMix * 0.45);
        result += highlightColor * highlightMix * 0.18;
    }

    FragColor = vec4(result, 1.0);
}