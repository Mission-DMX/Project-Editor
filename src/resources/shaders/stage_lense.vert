#version 410 core

// ---------- per‑instance attributes ----------
layout (location = 0) in vec3 aPos;      // centre
layout (location = 1) in vec3 aNormal;   // facing direction (must be normalized)
layout (location = 2) in float aRadius; // world radius
layout (location = 3) in vec3 aColor;    // linear RGB

// ---------- per‑vertex attributes (the quad) ----------
layout (location = 4) in vec2 aQuadOffset; // (-1,-1) .. (+1,+1)
layout (location = 5) in vec2 aQuadUV;     // (0,0) .. (1,1)

// ---------- outputs to fragment shader ----------
out vec2 vUV;          // local disc coordinates (0‑1)
out vec3 vColor;       // colour passed through
out float vRadius;     // radius (world units)
out vec3 vWorldPos;    // world position of the fragment (for depth, lighting, etc.)

// ---------- camera uniforms ----------
uniform mat4 uView;
uniform mat4 uProj;

void main()
{
    // ---- Build a tangent‑bitangent basis from the normal ----
    // Normalize defensively; a non-unit normal would stretch the disc into an
    // ellipse via the bitangent below.
    vec3 n = normalize(aNormal);
    // Choose an arbitrary vector that is not parallel to the normal.
    vec3 up = abs(n.z) < 0.999 ? vec3(0,0,1) : vec3(0,1,0);
    vec3 tangent   = normalize(cross(up, n));
    vec3 bitangent = cross(n, tangent); // unit because n and tangent are orthonormal

    // ---- Scale the quad to the disc radius ----
    // aQuadOffset is in [-1,1] range, so we multiply by 0.5 to get [-0.5,0.5]
    // then by the radius to get world units.
    vec2 localPos = (aQuadOffset * 0.5) * aRadius;

    // ---- Transform the local quad into world space ----
    vec3 worldPos = aPos
                  + tangent   * localPos.x
                  + bitangent * localPos.y;

    // ---- Pass data to the fragment shader ----
    vUV      = aQuadUV;          // (0,0) .. (1,1)
    vColor   = aColor;
    vRadius  = aRadius;
    vWorldPos = worldPos;

    // ---- Final clip‑space position ----
    gl_Position = uProj * uView * vec4(worldPos, 1.0);
}