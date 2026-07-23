"""3D OpenGL viewport for the stage visualizer.

Renders the scene in three passes (shadow maps, scene objects, volumetric
beam cones) and handles camera, picking and the name-label overlay.

"""

from __future__ import annotations

import ctypes
import json
import math
import os
import struct
import time
from logging import getLogger
from typing import TYPE_CHECKING, Any, override

import numpy as np
from OpenGL import GL as gl  # NOQA: N811 it is common practice to import is as lower case gl. Also it's not a const.
from PySide6 import QtCore, QtGui
from PySide6.QtOpenGLWidgets import QOpenGLWidget

if TYPE_CHECKING:
    from collections.abc import Sequence

    from OpenGL.constant import IntConstant
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QWidget

    from model.stage import StageConfig, StageObject

logger = getLogger(__name__)

MAX_SPOT_LIGHTS = 16    # maximum simultaneous spotlights in the scene shader
MAX_SHADOW_MAPS = 4     # shadow-casting lights (texture array layers)
SHADOW_MAP_SIZE = 1024  # per-layer shadow map resolution


class Model3D:
    """GPU mesh: VAO + VBO + EBO + index count."""

    def __init__(self, vao: int, vbo: int, ebo: int, index_count: int) -> None:
        """Initialize struct."""
        self.vao: int = vao
        self.vbo: int = vbo
        self.ebo: int = ebo
        self.index_count: int = index_count


class GltfNode:
    """A single node from a glTF scene graph."""

    def __init__(self,
                 name: str,
                 mesh_index: int,
                 children: list[int] | None,
                 translation: list[float] | None,
                 rotation: list[float] | None,
                 scale: list[float] | None) -> None:
        """Initialize the struct."""
        self.name: str = name or ""
        self.mesh_index: int = mesh_index
        self.children: list[int] = children or []
        self.translation: list[float] = translation or [0.0, 0.0, 0.0]
        self.rotation: list[float] = rotation or [0.0, 0.0, 0.0, 1.0]  # quaternion (x,y,z,w)
        self.scale: list[float] = scale or [1.0, 1.0, 1.0]


class GltfModel:
    """Minimal glTF/GLB container with node hierarchy and GPU meshes."""

    def __init__(self, nodes: list[GltfNode], scene_roots: list[int], mesh_primitives: dict[int, Model3D]) -> None:
        """Initialize the struct."""
        self.nodes: list[GltfNode] = nodes                    # list of GltfNode
        self.scene_roots: list[int] = scene_roots        # list of root node indices
        self.mesh_primitives: dict[int, Model3D] = mesh_primitives  # dict: mesh_index -> [Model3D]


class SpotLightData:
    """Spotlight data collected per frame from active MovingHeads."""

    __slots__ = ("color", "direction", "inner_cos", "outer_cos", "position")

    def __init__(self,
                 position: QtGui.QVector3D,
                 direction: QtGui.QVector3D,
                 color: tuple[float, float, float],
                 inner_deg: float=10.0,
                 outer_deg: float=18.0) -> None:
        """Initialize struct."""
        self.position: QtGui.QVector3D = position      # QVector3D
        self.direction: QtGui.QVector3D = direction    # QVector3D (normalized)
        self.color: tuple[float, float, float] = color  # (r, g, b) floats in [0, 1]
        self.inner_cos: float = math.cos(math.radians(inner_deg))
        self.outer_cos: float = math.cos(math.radians(outer_deg))


# glTF binary loading

# Mapping from glTF componentType to numpy dtype
_GLTF_COMPONENT_DTYPE = {
    5120: np.int8, 5121: np.uint8, 5122: np.int16,
    5123: np.uint16, 5125: np.uint32, 5126: np.float32,
}
# Mapping from glTF accessor type to number of components
_GLTF_TYPE_NUMCOMP = {
    "SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
    "MAT2": 4, "MAT3": 9, "MAT4": 16,
}


def _read_glb(path: str) -> tuple[dict[str, Any], bytes]:
    """Read a GLB file and return (json_dict, bin_chunk).

    GLB layout: 12-byte header + JSON chunk + BIN chunk.
    """
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 20:
        raise ValueError("GLB too small")
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2:
        raise ValueError("Invalid GLB")

    off = 12
    json_chunk = bin_chunk = None
    while off < length:
        chunk_len, chunk_type = struct.unpack_from("<I4s", data, off)
        off += 8
        chunk_data = data[off:off + chunk_len]
        off += chunk_len
        if chunk_type == b"JSON":
            json_chunk = chunk_data
        elif chunk_type in (b"BIN\x00", b"BIN"):
            bin_chunk = chunk_data

    if json_chunk is None or bin_chunk is None:
        raise ValueError("Invalid GLB: missing chunks")
    return json.loads(json_chunk.decode("utf-8")), bin_chunk


def _read_accessor(gltf: dict[str, Any], bin_chunk: bytes, acc_idx: int) -> np.ndarray:
    """Read a glTF accessor as a numpy array.

    Handles byte offsets, strides, component types, and normalization
    as specified by the glTF 2.0 standard.
    """
    acc = gltf["accessors"][acc_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    dt = _GLTF_COMPONENT_DTYPE[acc["componentType"]]
    comps = _GLTF_TYPE_NUMCOMP[acc["type"]]
    count = int(acc["count"])
    base = int(bv.get("byteOffset", 0)) + int(acc.get("byteOffset", 0))
    stride = bv.get("byteStride")
    item_size = np.dtype(dt).itemsize * comps

    if stride is None or int(stride) == item_size:
        # Read directly
        flat = np.frombuffer(bin_chunk, dtype=dt, count=count * comps, offset=base)
        out = flat.reshape((count, comps))
    else:
        # Read element by element
        stride = int(stride)
        out = np.empty((count, comps), dtype=dt)
        for i in range(count):
            out[i, :] = np.frombuffer(bin_chunk, dtype=dt, count=comps,
                                      offset=base + i * stride)

    # Apply normalization for integer types (glTF spec)
    if acc.get("normalized") and np.issubdtype(out.dtype, np.integer):
        out = out.astype(np.float32) / float(np.iinfo(out.dtype).max)

    return out


def _compute_vertex_normals(positions: np.ndarray, indices: np.ndarray) -> np.ndarray:
    """Compute smooth vertex normals by averaging face normals.

    Used as fallback when the glTF model does not provide NORMAL attributes.
    """
    normals = np.zeros_like(positions, dtype=np.float32)
    tris = indices.reshape((-1, 3))
    p0, p1, p2 = positions[tris[:, 0]], positions[tris[:, 1]], positions[tris[:, 2]]
    # Face normals via cross product
    n = np.cross(p1 - p0, p2 - p0)
    # Accumulate face normals at each vertex
    for k in range(3):
        np.add.at(normals, tris[:, k], n)
    # Normalize
    lens = np.linalg.norm(normals, axis=1)
    lens[lens == 0.0] = 1.0
    normals /= lens[:, None]
    return normals


def _upload_mesh(vertex_data: np.ndarray, indices: np.ndarray) -> Model3D:
    """Upload interleaved position+normal vertex data to the GPU.

    Vertex layout: [pos_x, pos_y, pos_z, norm_x, norm_y, norm_z] (6 floats).
    Returns a Model3D with the GPU handles.
    """
    vertex_data = np.ascontiguousarray(vertex_data, dtype=np.float32)
    indices = np.ascontiguousarray(indices, dtype=np.uint32)
    vao = gl.glGenVertexArrays(1)
    vbo = gl.glGenBuffers(1)
    ebo = gl.glGenBuffers(1)
    gl.glBindVertexArray(vao)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, gl.GL_STATIC_DRAW)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
    stride = 6 * 4  # 6 floats * 4 bytes
    gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))
    gl.glEnableVertexAttribArray(0)
    gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(12))
    gl.glEnableVertexAttribArray(1)
    gl.glBindVertexArray(0)
    return Model3D(vao, vbo, ebo, int(indices.size))


def _load_gltf_model(path: str) -> GltfModel:
    """Load a GLB file, build the node hierarchy, and upload all meshes.

    Returns a GltfModel containing the scene graph and GPU mesh handles.
    """
    gltf, bin_chunk = _read_glb(path)

    # Build node list
    nodes = [GltfNode(n.get("name", ""), n.get("mesh"), n.get("children") or [],
                       n.get("translation"), n.get("rotation"), n.get("scale"))
             for n in gltf.get("nodes", [])]

    # Determine scene root nodes
    si = int(gltf.get("scene", 0))
    scenes = gltf.get("scenes", [])
    scene_roots = (scenes[si].get("nodes", [])
                   if scenes and 0 <= si < len(scenes)
                   else list(range(len(nodes))))

    # Upload mesh primitives to GPU
    mesh_prims = {}
    for mi, mesh in enumerate(gltf.get("meshes", [])):
        plist = []
        for prim in mesh.get("primitives", []) or []:
            attrs = prim.get("attributes", {})
            if "POSITION" not in attrs:
                continue
            pos = _read_accessor(gltf, bin_chunk, attrs["POSITION"]).astype(np.float32)
            nrm = (_read_accessor(gltf, bin_chunk, attrs["NORMAL"]).astype(np.float32)
                   if "NORMAL" in attrs else None)
            idx = (_read_accessor(gltf, bin_chunk, prim["indices"]).reshape(-1).astype(np.uint32)
                   if "indices" in prim
                   else np.arange(pos.shape[0], dtype=np.uint32))
            if nrm is None or nrm.shape[0] != pos.shape[0]:
                nrm = _compute_vertex_normals(pos, idx)
            plist.append(_upload_mesh(np.concatenate([pos[:, :3], nrm[:, :3]], axis=1), idx))
        if plist:
            mesh_prims[mi] = plist

    return GltfModel(nodes, scene_roots, mesh_prims)


def _compile_shader(src: bytes, stype: IntConstant) -> int:
    """Compile a single GLSL shader and raise on error."""
    s = gl.glCreateShader(stype)
    gl.glShaderSource(s, src)
    gl.glCompileShader(s)
    if gl.glGetShaderiv(s, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
        log = gl.glGetShaderInfoLog(s)
        kind = "vertex" if stype == gl.GL_VERTEX_SHADER else "fragment"
        raise RuntimeError(f"{kind} shader failed: {log}")
    return s


def _link_program(vs_src: bytes, fs_src: bytes) -> int:
    """Compile vertex + fragment shaders and link into a program."""
    vs = _compile_shader(vs_src, gl.GL_VERTEX_SHADER)
    fs = _compile_shader(fs_src, gl.GL_FRAGMENT_SHADER)
    prog = gl.glCreateProgram()
    gl.glAttachShader(prog, vs)
    gl.glAttachShader(prog, fs)
    gl.glLinkProgram(prog)
    if gl.glGetProgramiv(prog, gl.GL_LINK_STATUS) != gl.GL_TRUE:
        raise RuntimeError(f"link failed: {gl.glGetProgramInfoLog(prog)}")
    gl.glDeleteShader(vs)
    gl.glDeleteShader(fs)
    return prog


# Depth-only shader (Pass 0: shadow map generation)

DEPTH_VS = b"""
#version 410 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;  // unused but matches VAO layout
uniform mat4 lightSpaceMatrix;
uniform mat4 model;
void main() {
    gl_Position = lightSpaceMatrix * model * vec4(aPos, 1.0);
}
"""

DEPTH_FS = b"""
#version 410 core
void main() {
    // depth is written automatically
}
"""

# Scene shader (Pass 1: Phong + spotlights + PCF shadows)

SCENE_VS = b"""
#version 410 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 FragPos;
out vec3 Normal;

void main() {
    vec4 wp = model * vec4(aPos, 1.0);
    FragPos = wp.xyz;
    Normal = mat3(transpose(inverse(model))) * aNormal;
    gl_Position = projection * view * wp;
}
"""

SCENE_FS = ("""
#version 410 core

#define MAX_LIGHTS """ + str(MAX_SPOT_LIGHTS) + """
#define MAX_SHADOWS """ + str(MAX_SHADOW_MAPS) + """

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
""").encode("utf-8")


# Beam shader (Pass 2: volumetric cone with ray-marched shadows)

BEAM_VS = b"""
#version 410 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec3 LocalPos;
out vec3 WorldPos;

void main() {
    LocalPos = aPos;
    vec4 wp = model * vec4(aPos, 1.0);
    WorldPos = wp.xyz;
    gl_Position = projection * view * wp;
}
"""

BEAM_FS = b"""
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
"""


class Stage3DWidget(QOpenGLWidget):
    """OpenGL 3D viewport for the stage visualizer."""

    # Emitted when user left-clicks a fixture in 3D
    fixture_clicked = QtCore.Signal(str)
    # Emitted when user right-clicks (deselect all)
    deselect_all_requested = QtCore.Signal()

    def __init__(self, stage_config: StageConfig, parent: QWidget | None=None) -> None:
        """Initialize using given stage configuration and parent."""
        super().__init__(parent)
        self._stage_config = stage_config

        # Shader programs (initialized in initializeGL)
        self._scene_program = None
        self._beam_program = None
        self._depth_program = None

        # Uniform location caches
        self._sc = {}             # scene shader uniforms
        self._sc_light_locs = []  # per-light uniform locations
        self._bm = {}             # beam shader uniforms
        self._dp = {}             # depth shader uniforms

        # Shadow map GPU resources
        self._shadow_fbo = None
        self._shadow_tex = None

        # Projection matrix
        self._projection = QtGui.QMatrix4x4()

        # Camera state (orbit mode)
        self._camera_target = QtGui.QVector3D(0.0, 10.0, 0.0)
        self._camera_up = QtGui.QVector3D(0.0, 1.0, 0.0)
        self._camera_pos = QtGui.QVector3D(0.0, 200.0, 400.0)
        self._cam_yaw = -90.0
        self._cam_pitch = -20.0
        self._cam_distance = (self._camera_pos - self._camera_target).length()

        # Input state
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self._mouse_last_pos = None
        self._mouse_press_pos = None
        self._mouse_buttons = set()
        self._keys_down = set()
        self._move_speed = 400.0
        self._boost_speed = 1200.0

        # Camera movement timer (~60 Hz)
        self._camera_timer = QtCore.QTimer(self)
        self._camera_timer.timeout.connect(self._tick_camera)
        self._camera_timer.start(16)

        # Model caches
        self._models: dict[str, Model3D] = {}       # path -> Model3D (OBJ meshes)
        self._gltf_models: dict[str, GltfModel] = {}  # path -> GltfModel
        self._beam_cone = None
        self._ground_plane = None

        # Selection highlight state
        self._selected_object_ids = set()
        self._highlight_is_multi = False  # True = orange, False = neon-yellow

        # F-key overlay toggle
        self._show_labels = False

        # FPS counter
        self._fps_frame_count = 0
        self._fps_last_time = time.time()
        self._fps_display = 0.0

    # OpenGL initialization

    @override
    def initializeGL(self) -> None:
        gl.glClearColor(0.02, 0.02, 0.03, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)

        # Compile and link shader programs
        try:
            self._scene_program = _link_program(SCENE_VS, SCENE_FS)
        except RuntimeError as e:
            logger.error("Scene shader: %s", e)
            return
        try:
            self._beam_program = _link_program(BEAM_VS, BEAM_FS)
        except RuntimeError as e:
            logger.error("Beam shader: %s", e)
        try:
            self._depth_program = _link_program(DEPTH_VS, DEPTH_FS)
        except RuntimeError as e:
            logger.error("Depth shader: %s", e)

        # Cache uniform locations for each program

        # Scene shader
        sp = self._scene_program
        for name in ("projection", "view", "model", "viewPos", "baseColor",
                      "ambientLevel", "numLights", "numShadowLights", "shadowMap",
                      "highlightMix", "highlightColor"):
            self._sc[name] = gl.glGetUniformLocation(sp, name)

        # Per-light uniforms (spotlight array)
        self._sc_light_locs = []
        for i in range(MAX_SPOT_LIGHTS):
            p = f"lights[{i}]."
            self._sc_light_locs.append({
                k: gl.glGetUniformLocation(sp, p + k)
                for k in ("position", "direction", "color", "innerCos", "outerCos")
            })

        # Light-space matrix array for shadow mapping
        self._sc_lsm_locs = [
            gl.glGetUniformLocation(sp, f"lightSpaceMatrices[{i}]")
            for i in range(MAX_SHADOW_MAPS)
        ]

        # Beam shader
        bp = self._beam_program
        if bp:
            for name in ("projection", "view", "model", "beamColor",
                         "beamLightSpaceMatrix", "shadowMap", "beamShadowLayer",
                         "hasShadow", "beamLightPos"):
                self._bm[name] = gl.glGetUniformLocation(bp, name)

        # Depth shader
        dp = self._depth_program
        if dp:
            self._dp["lightSpaceMatrix"] = gl.glGetUniformLocation(dp, "lightSpaceMatrix")
            self._dp["model"] = gl.glGetUniformLocation(dp, "model")

        # Create shadow map resources
        self._init_shadow_map_resources()

        # Create geometry
        self._beam_cone = self._create_unit_cone(64)
        self._ground_plane = self._create_ground_plane(2000.0)

        # Load 3D models for all existing stage objects
        for obj in self._stage_config.objects:
            self._ensure_models_loaded(obj)

        logger.info("OpenGL init done. %d objects.", len(self._stage_config.objects))

    def _init_shadow_map_resources(self) -> None:
        """Create the FBO and 2D texture array for shadow maps.

        Each shadow-casting light gets one layer in the texture array.
        The FBO is reused for all layers by rebinding the depth attachment.
        """
        if self._depth_program is None:
            return

        # Create depth texture array
        self._shadow_tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._shadow_tex)
        gl.glTexImage3D(
            gl.GL_TEXTURE_2D_ARRAY, 0, gl.GL_DEPTH_COMPONENT24,
            SHADOW_MAP_SIZE, SHADOW_MAP_SIZE, MAX_SHADOW_MAPS,
            0, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, None
        )
        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
        # Border color = max depth so areas outside shadow map are fully lit
        gl.glTexParameterfv(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_BORDER_COLOR,
                            (gl.GLfloat * 4)(1.0, 1.0, 1.0, 1.0))
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, 0)

        # Create FBO and attach layer 0 initially
        self._shadow_fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._shadow_fbo)
        gl.glFramebufferTextureLayer(
            gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT,
            self._shadow_tex, 0, 0
        )
        gl.glDrawBuffer(gl.GL_NONE)
        gl.glReadBuffer(gl.GL_NONE)

        status = gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER)
        if status != gl.GL_FRAMEBUFFER_COMPLETE:
            logger.error("Shadow FBO incomplete: %s", status)
            self._shadow_fbo = None

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    @override
    def resizeGL(self, w: int, h: int) -> None:
        gl.glViewport(0, 0, w, h)
        self._projection = QtGui.QMatrix4x4()
        self._projection.perspective(45.0, w / max(h, 1), 1.0, 15000.0)

    # Main render loop (paintGL)

    @override
    def paintGL(self) -> None:
        if self._scene_program is None:
            return

        # Reset GL state
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glDisable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthMask(gl.GL_TRUE)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_BACK)

        self._update_camera_pos()
        view = QtGui.QMatrix4x4()
        view.lookAt(self._camera_pos, self._camera_target, self._camera_up)

        proj_data = self._projection.copyDataTo()
        view_data = view.copyDataTo()

        spotlights, beam_list = self._collect_lights_and_beams()

        # PASS 0: Shadow maps
        light_space_matrices = self._render_shadow_maps(spotlights)

        # Restore widget's default FBO and viewport
        default_fbo = self.defaultFramebufferObject()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, default_fbo)
        gl.glViewport(0, 0, self.width(), self.height())
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # PASS 1: Scene objects (Phong + spotlights + shadows)
        gl.glUseProgram(self._scene_program)
        gl.glUniformMatrix4fv(self._sc["projection"], 1, gl.GL_TRUE, proj_data)
        gl.glUniformMatrix4fv(self._sc["view"], 1, gl.GL_TRUE, view_data)
        cam = self._camera_pos
        gl.glUniform3f(self._sc["viewPos"], cam.x(), cam.y(), cam.z())
        gl.glUniform1f(self._sc["ambientLevel"], 0.09)

        # Upload spotlight data to shader
        num_lights = min(len(spotlights), MAX_SPOT_LIGHTS)
        gl.glUniform1i(self._sc["numLights"], num_lights)
        for i in range(num_lights):
            sl = spotlights[i]
            locs = self._sc_light_locs[i]
            gl.glUniform3f(locs["position"], sl.position.x(), sl.position.y(), sl.position.z())
            gl.glUniform3f(locs["direction"], sl.direction.x(), sl.direction.y(), sl.direction.z())
            gl.glUniform3f(locs["color"], sl.color[0], sl.color[1], sl.color[2])
            gl.glUniform1f(locs["innerCos"], sl.inner_cos)
            gl.glUniform1f(locs["outerCos"], sl.outer_cos)

        # Upload shadow data
        num_shadow = min(len(light_space_matrices), MAX_SHADOW_MAPS)
        gl.glUniform1i(self._sc["numShadowLights"], num_shadow)
        for i, lsm in enumerate(light_space_matrices):
            gl.glUniformMatrix4fv(self._sc_lsm_locs[i], 1, gl.GL_TRUE, lsm.copyDataTo())

        # Bind shadow map texture array to texture unit 0
        gl.glActiveTexture(gl.GL_TEXTURE0)
        if self._shadow_tex is not None:
            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._shadow_tex)
        gl.glUniform1i(self._sc["shadowMap"], 0)

        # Draw ground plane
        if self._ground_plane:
            gl.glUniformMatrix4fv(self._sc["model"], 1, gl.GL_TRUE, QtGui.QMatrix4x4().copyDataTo())
            gl.glUniform3f(self._sc["baseColor"], 0.15, 0.15, 0.15)
            gl.glUniform1f(self._sc["highlightMix"], 0.0)
            gl.glBindVertexArray(self._ground_plane.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, self._ground_plane.index_count, gl.GL_UNSIGNED_INT, None)

        # Draw stage objects with selection highlighting
        hl_color = (1.0, 0.55, 0.1) if self._highlight_is_multi else (1.0, 0.95, 0.15)
        # warm orange for multi/group else neon yellow for single
        gl.glUniform3f(self._sc["highlightColor"], *hl_color)

        for idx, obj in enumerate(self._stage_config.objects):
            is_selected = (obj.id in self._selected_object_ids)
            # Alternate object colors for visual distinction
            color = (0.50, 0.50, 0.55) if idx % 2 == 0 else (0.45, 0.45, 0.50)
            gl.glUniform1f(self._sc["highlightMix"], 1.0 if is_selected else 0.0)
            self._draw_stage_object(obj, color)

        gl.glBindVertexArray(0)
        gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, 0)

        # PASS 2: Volumetric beam cones
        if beam_list and self._beam_program and self._beam_cone:
            self._draw_all_beams(beam_list, proj_data, view_data,
                                spotlights, light_space_matrices)

        gl.glUseProgram(0)

        # Overlays (QPainter on top of GL)
        if self._show_labels:
            self._draw_fixture_labels(view)

        self._update_fps()
        self._draw_fps_counter()

    # Pass 0: Shadow map rendering

    def _render_shadow_maps(self, spotlights: list[SpotLightData]) -> list[QtGui.QMatrix4x4]:
        """Render depth from each spotlight's POV into the shadow texture array.

        Returns:
            List of light-space matrices (one per shadow-casting light).

        """
        if not spotlights or self._shadow_fbo is None or self._depth_program is None:
            return []

        light_space_matrices = []
        num = min(len(spotlights), MAX_SHADOW_MAPS)

        gl.glUseProgram(self._depth_program)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._shadow_fbo)
        gl.glViewport(0, 0, SHADOW_MAP_SIZE, SHADOW_MAP_SIZE)

        # Polygon offset reduces self-shadowing artifacts (shadow acne)
        gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)
        gl.glPolygonOffset(1.0, 1.0)

        for i in range(num):
            sl = spotlights[i]
            lsm = self._compute_light_space_matrix(sl)
            light_space_matrices.append(lsm)

            # Attach this layer of the texture array to the FBO
            gl.glFramebufferTextureLayer(
                gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT,
                self._shadow_tex, 0, i
            )
            gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

            gl.glUniformMatrix4fv(self._dp["lightSpaceMatrix"], 1, gl.GL_TRUE, lsm.copyDataTo())
            self._draw_scene_depth_only()

        gl.glDisable(gl.GL_POLYGON_OFFSET_FILL)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glUseProgram(0)

        return light_space_matrices

    def _compute_light_space_matrix(self, spotlight: SpotLightData) -> QtGui.QMatrix4x4:
        """Build a perspective projection matrix from a spotlight's POV.

        The FOV is derived from the spotlight's outer cone angle to ensure
        the shadow map fully covers the illuminated area.
        """
        pos = spotlight.position
        d = spotlight.direction
        target = pos + d * 500.0

        # Pick an up vector that isn't parallel to the light direction
        up = QtGui.QVector3D(0.0, 1.0, 0.0)
        if abs(QtGui.QVector3D.dotProduct(up, d)) > 0.95:
            up = QtGui.QVector3D(1.0, 0.0, 0.0)

        view = QtGui.QMatrix4x4()
        view.lookAt(pos, target, up)

        # FOV from outer cone angle, clamped to reasonable range
        half_angle = math.degrees(math.acos(max(spotlight.outer_cos, 0.01)))
        fov = min(130.0, max(40.0, half_angle * 3.0))

        proj = QtGui.QMatrix4x4()
        proj.perspective(fov, 1.0, 0.5, 800.0)

        result = QtGui.QMatrix4x4(proj)
        result *= view
        return result

    def _draw_scene_depth_only(self) -> None:
        """Draw all scene objects with the depth shader (for shadow maps)."""
        for obj in self._stage_config.objects:
            base = self._build_base_model_matrix(obj)
            for entry in getattr(obj, "get_model_entries", list)():
                model = QtGui.QMatrix4x4(base)
                self._apply_local_ops(model, getattr(entry, "local_ops", ()))

                if entry.model_path in self._gltf_models:
                    self._traverse_gltf(entry.model_path, model, obj,
                                        model_loc=self._dp["model"])
                elif entry.model_path in self._models:
                    gl.glUniformMatrix4fv(self._dp["model"], 1, gl.GL_TRUE, model.copyDataTo())
                    m = self._models[entry.model_path]
                    gl.glBindVertexArray(m.vao)
                    gl.glDrawElements(gl.GL_TRIANGLES, m.index_count, gl.GL_UNSIGNED_INT, None)

        gl.glBindVertexArray(0)

    # Shared rendering helpers

    def _build_base_model_matrix(self, obj: StageObject) -> QtGui.QMatrix4x4:
        """Build the T * Rz * Ry * Rx * S model matrix for a stage object."""
        m = QtGui.QMatrix4x4()
        m.translate(obj.position[0], obj.position[1], obj.position[2])
        m.rotate(obj.rotation[2], 0.0, 0.0, 1.0)
        m.rotate(obj.rotation[1], 0.0, 1.0, 0.0)
        m.rotate(obj.rotation[0], 1.0, 0.0, 0.0)
        m.scale(float(getattr(obj, "scale", 1.0)))
        return m

    def _get_overrides(self, stage_obj: StageObject) -> dict[str, tuple[float, float, float, float]]:
        """Get glTF node rotation overrides (pan/tilt) from a stage object."""
        if stage_obj and hasattr(stage_obj, "get_gltf_node_overrides"):
            try:
                return stage_obj.get_gltf_node_overrides() or {}
            except Exception as e:
                logger.exception("Unable to extract GLTF overrides from model (%s) : %s", str(stage_obj), str(e))
        return {}

    def _node_local_matrix(self,
                           node: GltfNode,
                           overrides: dict[str, tuple[float, float, float, float]]) -> QtGui.QMatrix4x4:
        """Compute the local transform matrix for a glTF node.

        Applies translation, quaternion rotation, optional pan/tilt override,
        and scale — matching the glTF 2.0 transform specification.
        """
        m = QtGui.QMatrix4x4()
        t, r, s = node.translation, node.rotation, node.scale
        m.translate(float(t[0]), float(t[1]), float(t[2]))
        # glTF quaternion: (x, y, z, w)
        q = QtGui.QQuaternion(float(r[3]), float(r[0]), float(r[1]), float(r[2]))
        m.rotate(q)
        # Apply axis-angle override if this node has one (for pan/tilt)
        if node.name in overrides:
            ax, ay, az, deg = overrides[node.name]
            m.rotate(float(deg), float(ax), float(ay), float(az))
        m.scale(float(s[0]), float(s[1]), float(s[2]))
        return m

    def _traverse_gltf(self,
                       model_path: str,
                       base_model: QtGui.QMatrix4x4,
                       stage_obj: StageObject,
                       model_loc: int,
                       color: tuple[float, float, float] | None = None,
                       color_loc: tuple[float, float, float] | None = None) -> None:
        """Traverse the glTF node hierarchy and draw each mesh.

        Uses an iterative stack-based depth-first traversal instead of
        recursion. Works for both the scene shader (with color) and the
        depth shader (without color).

        """
        gm = self._gltf_models.get(model_path)
        if gm is None:
            return
        overrides = self._get_overrides(stage_obj)

        # Stack of (node_index, parent_world_matrix)
        stack = [(int(r), QtGui.QMatrix4x4(base_model)) for r in gm.scene_roots]
        while stack:
            ni, parent = stack.pop()
            if ni < 0 or ni >= len(gm.nodes):
                continue
            node = gm.nodes[ni]
            world = QtGui.QMatrix4x4(parent)
            world *= self._node_local_matrix(node, overrides)

            # Draw mesh primitives at this node
            if node.mesh_index is not None and int(node.mesh_index) in gm.mesh_primitives:
                gl.glUniformMatrix4fv(model_loc, 1, gl.GL_TRUE, world.copyDataTo())
                if color and color_loc is not None:
                    gl.glUniform3f(color_loc, color[0], color[1], color[2])
                for prim in gm.mesh_primitives[int(node.mesh_index)]:
                    gl.glBindVertexArray(prim.vao)
                    gl.glDrawElements(gl.GL_TRIANGLES, prim.index_count, gl.GL_UNSIGNED_INT, None)

            # Push children (reversed so left children are processed first)
            stack.extend((int(child), world) for child in reversed(node.children or []))

    # Pass 1: Scene object drawing

    def _draw_stage_object(self, obj: StageObject, color: tuple[float, float, float]) -> None:
        """Draw a single stage object with the scene shader."""
        base = self._build_base_model_matrix(obj)
        gl.glUniform3f(self._sc["baseColor"], color[0], color[1], color[2])

        for entry in getattr(obj, "get_model_entries", list)():
            model = QtGui.QMatrix4x4(base)
            self._apply_local_ops(model, getattr(entry, "local_ops", ()))

            if entry.model_path in self._gltf_models:
                self._traverse_gltf(entry.model_path, model, obj,
                                    model_loc=self._sc["model"],
                                    color=color, color_loc=self._sc["baseColor"])
            elif entry.model_path in self._models:
                gl.glUniformMatrix4fv(self._sc["model"], 1, gl.GL_TRUE, model.copyDataTo())
                m = self._models[entry.model_path]
                gl.glBindVertexArray(m.vao)
                gl.glDrawElements(gl.GL_TRIANGLES, m.index_count, gl.GL_UNSIGNED_INT, None)

    # Pass 2: Beam rendering

    def _draw_all_beams(self,
                        beam_list: list[tuple[QtGui.QVector3D, QtGui.QVector3D, tuple[float, float, float], float]],
                        proj_data: Sequence[float],
                        view_data: Sequence[float],
                        spotlights: list[SpotLightData],
                        light_space_matrices: list[QtGui.QMatrix4x4]) -> None:
        """Draw all volumetric beam cones with additive blending.

        The depth buffer from Pass 1 (ground plane) naturally prevents
        beam fragments below the floor from being visible, giving a
        proper elliptical intersection where the cone meets the ground.
        """
        gl.glUseProgram(self._beam_program)
        gl.glUniformMatrix4fv(self._bm["projection"], 1, gl.GL_TRUE, proj_data)
        gl.glUniformMatrix4fv(self._bm["view"], 1, gl.GL_TRUE, view_data)

        # Bind shadow map to texture unit 1 (unit 0 is used by the scene pass)
        has_shadow = (self._shadow_tex is not None and len(light_space_matrices) > 0)
        if has_shadow:
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._shadow_tex)
            gl.glUniform1i(self._bm["shadowMap"], 1)

        # Enable additive blending and disable backface culling for cones
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDepthMask(gl.GL_FALSE)
        gl.glEnable(gl.GL_DEPTH_TEST)

        gl.glBindVertexArray(self._beam_cone.vao)

        max_beam_length = 500.0

        for beam_idx, (origin, direction, color, _dimmer) in enumerate(beam_list):
            actual_length = max_beam_length
            # Cone radius matches the spotlight's outer cone angle so that the
            # volumetric beam lines up with the lit area on the scene.
            if beam_idx < len(spotlights):
                outer_cos = spotlights[beam_idx].outer_cos
                half_angle_rad = math.acos(max(outer_cos, 0.01))
            else:
                half_angle_rad = math.radians(18.0)
            actual_radius = float(math.tan(half_angle_rad) * actual_length)

            mat = self._build_cone_matrix(origin, direction, actual_length, actual_radius)
            gl.glUniformMatrix4fv(self._bm["model"], 1, gl.GL_TRUE, mat.copyDataTo())
            gl.glUniform3f(self._bm["beamColor"], color[0], color[1], color[2])

            # Upload per-beam shadow data
            shadow_layer = beam_idx
            if has_shadow and shadow_layer < len(light_space_matrices):
                gl.glUniform1i(self._bm["hasShadow"], 1)
                gl.glUniform1i(self._bm["beamShadowLayer"], shadow_layer)
                gl.glUniformMatrix4fv(
                    self._bm["beamLightSpaceMatrix"], 1, gl.GL_TRUE,
                    light_space_matrices[shadow_layer].copyDataTo())
            else:
                gl.glUniform1i(self._bm["hasShadow"], 0)

            # Light origin for the volumetric shadow ray-march.
            gl.glUniform3f(self._bm["beamLightPos"],
                           origin.x(), origin.y(), origin.z())

            gl.glDrawElements(gl.GL_TRIANGLES, self._beam_cone.index_count, gl.GL_UNSIGNED_INT, None)

        # Restore GL state
        gl.glBindVertexArray(0)
        gl.glDepthMask(gl.GL_TRUE)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glDisable(gl.GL_BLEND)

        if has_shadow:
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, 0)
            gl.glActiveTexture(gl.GL_TEXTURE0)

    def _build_cone_matrix(self, origin: QtGui.QVector3D, direction: QtGui.QVector3D,
                           length: float, radius: float) -> QtGui.QMatrix4x4:
        """Build a model matrix that places the unit cone (tip=origin, base along direction).

        Constructs a rotation matrix from a local coordinate frame
        (right, up, forward) and applies translation + non-uniform scaling.
        """
        fwd = QtGui.QVector3D(direction)
        if fwd.length() < 1e-6:
            fwd = QtGui.QVector3D(0.0, -1.0, 0.0)
        else:
            fwd.normalize()

        # Build orthonormal basis
        up = QtGui.QVector3D(0.0, 1.0, 0.0)
        if abs(QtGui.QVector3D.dotProduct(up, fwd)) > 0.95:
            up = QtGui.QVector3D(1.0, 0.0, 0.0)

        right = QtGui.QVector3D.crossProduct(up, fwd)
        right.normalize()
        up2 = QtGui.QVector3D.crossProduct(fwd, right)
        up2.normalize()

        # Build rotation matrix from basis vectors
        rot = QtGui.QMatrix4x4()
        rot.setColumn(0, QtGui.QVector4D(right, 0.0))
        rot.setColumn(1, QtGui.QVector4D(up2, 0.0))
        rot.setColumn(2, QtGui.QVector4D(-fwd, 0.0))
        rot.setColumn(3, QtGui.QVector4D(0.0, 0.0, 0.0, 1.0))

        m = QtGui.QMatrix4x4()
        m.translate(origin)
        m *= rot
        m.scale(float(radius), float(radius), float(length))
        return m

    # Light and beam collection

    def _collect_lights_and_beams(self) \
            -> tuple[list[SpotLightData],
            list[tuple[QtGui.QVector3D, QtGui.QVector3D, tuple[float, float, float], float]]]:
        """Collect spotlight data and beam parameters from all active MovingHeads.

        For each moving head with ``beam_on == True``, computes the world-space
        beam origin (from the BeamOrigin node) and direction (from BeamOrigin
        toward the tilt pivot), then creates both a SpotLightData (for scene
        lighting) and a beam tuple (for volumetric rendering).
        """
        spotlights = []
        beam_list = []

        try:
            from model.stage import MovingHead
            beam_origin_name = MovingHead.BEAM_ORIGIN_NODE_NAME
            tilt_node_name = MovingHead.TILT_NODE_NAME
        except Exception:
            beam_origin_name = "BeamOrigin"
            tilt_node_name = "Cylinder.018"

        for obj in getattr(self._stage_config, "objects", []):
            is_mh = hasattr(obj, "pan") and hasattr(obj, "tilt") and hasattr(obj, "beam_on")
            if not is_mh or not bool(getattr(obj, "beam_on", False)):
                continue

            base = self._build_base_model_matrix(obj)
            entries = getattr(obj, "get_model_entries", list)()
            if not entries:
                continue
            model_path = entries[0].model_path

            # Find world-space position of the BeamOrigin node
            origin_mat = self._find_gltf_node_world(model_path, base, obj, beam_origin_name)
            if origin_mat is None:
                origin_mat = QtGui.QMatrix4x4(base)
            origin_pos = origin_mat.map(QtGui.QVector3D(0.0, 0.0, 0.0))

            # Find world-space position of the tilt pivot node
            tilt_mat = self._find_gltf_node_world(model_path, base, obj, tilt_node_name)

            # Beam direction: from tilt pivot toward BeamOrigin (lens).
            # Pan/tilt naturally rotates this since BeamOrigin moves with the head.
            if tilt_mat is not None:
                tilt_pos = tilt_mat.map(QtGui.QVector3D(0.0, 0.0, 0.0))
                dir_vec = origin_pos - tilt_pos
                if dir_vec.length() < 1e-6:
                    dir_vec = QtGui.QVector3D(0.0, -1.0, 0.0)
                else:
                    dir_vec.normalize()
            else:
                dir_vec = QtGui.QVector3D(0.0, -1.0, 0.0)

            # Convert beam color from 0-255 int to 0-1 float, apply dimmer
            rgb = getattr(obj, "beam_color", (255, 255, 255))
            dimmer = max(0.0, min(1.0, float(getattr(obj, "dimmer", 1.0))))
            color_f = (
                float(rgb[0]) / 255.0 * dimmer,
                float(rgb[1]) / 255.0 * dimmer,
                float(rgb[2]) / 255.0 * dimmer,
            )

            spotlights.append(SpotLightData(
                position=origin_pos, direction=dir_vec, color=color_f,
                inner_deg=8.0, outer_deg=16.0,
            ))
            beam_list.append((origin_pos, dir_vec, color_f, dimmer))

        return spotlights, beam_list

    # Geometry creation

    def _create_unit_cone(self, segments: int=48) -> Model3D:
        """Create a unit cone mesh (tip at origin, base ring at z=-1).

        Used for beam rendering. Normals point outward from the cone surface.
        """
        seg = max(3, segments)
        verts, idx = [], []
        # Tip vertex at origin (index 0)
        verts.extend([0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
        # Base ring vertices
        for i in range(seg):
            a = (i / seg) * 2.0 * math.pi
            x, y = math.cos(a), math.sin(a)
            length = math.sqrt(x * x + y * y + 0.09)
            verts.extend([x, y, -1.0, x / length, y / length, 0.3 / length])
        # Triangle fan from tip to base ring
        for i in range(seg):
            idx.extend([0, 1 + i, 1 + (i + 1) % seg])
        v = np.array(verts, dtype=np.float32)
        ii = np.array(idx, dtype=np.uint32)
        return self._upload_vao(v, ii)

    def _create_ground_plane(self, size: float=2000.0) -> Model3D:
        """Create a flat ground plane quad at y=0 with upward normals."""
        h = size / 2.0
        v = np.array([
            -h, 0, -h, 0, 1, 0,  h, 0, -h, 0, 1, 0,
             h, 0,  h, 0, 1, 0, -h, 0,  h, 0, 1, 0,
        ], dtype=np.float32)
        ii = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        return self._upload_vao(v, ii)

    def _upload_vao(self, verts: np.ndarray, indices: np.ndarray) -> Model3D:
        """Upload interleaved position+normal vertex data to a new VAO."""
        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        ebo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)
        return Model3D(vao, vbo, ebo, int(indices.size))

    # Camera controls

    def _update_camera_pos(self) -> None:
        """Compute camera position from orbit parameters (yaw, pitch, distance)."""
        yaw = math.radians(self._cam_yaw)
        pitch = math.radians(self._cam_pitch)
        cy = math.cos(pitch)
        fwd = QtGui.QVector3D(
            float(math.cos(yaw) * cy), float(math.sin(pitch)), float(math.sin(yaw) * cy))
        self._camera_pos = self._camera_target - fwd * float(self._cam_distance)

    def _tick_camera(self) -> None:
        """Process WASD/arrow key camera movement at ~60 Hz."""
        if not self.isVisible():
            return
        if self._keys_down:
            dt = 0.016
            speed = (self._boost_speed if QtCore.Qt.Key.Key_Shift in self._keys_down
                     else self._move_speed)
            yaw = math.radians(self._cam_yaw)
            fwd = QtGui.QVector3D(float(math.cos(yaw)), 0.0, float(math.sin(yaw)))
            if fwd.length() == 0:
                fwd = QtGui.QVector3D(0, 0, -1)
            fwd.normalize()
            right = QtGui.QVector3D.crossProduct(fwd, self._camera_up)
            right.normalize()
            move = QtGui.QVector3D(0, 0, 0)
            if QtCore.Qt.Key.Key_W in self._keys_down or QtCore.Qt.Key.Key_Up in self._keys_down:
                move += fwd
            if QtCore.Qt.Key.Key_S in self._keys_down or QtCore.Qt.Key.Key_Down in self._keys_down:
                move -= fwd
            if QtCore.Qt.Key.Key_D in self._keys_down or QtCore.Qt.Key.Key_Right in self._keys_down:
                move += right
            if QtCore.Qt.Key.Key_A in self._keys_down or QtCore.Qt.Key.Key_Left in self._keys_down:
                move -= right
            if QtCore.Qt.Key.Key_E in self._keys_down:
                move += self._camera_up
            if QtCore.Qt.Key.Key_Q in self._keys_down:
                move -= self._camera_up
            if move.length() > 0:
                move.normalize()
                self._camera_target += move * float(speed * dt)
        # main 60 Hz render loop
        self.update()

    # Mouse and keyboard input

    @override
    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        self._mouse_last_pos = e.position().toPoint()
        self._mouse_press_pos = e.position().toPoint()
        self._mouse_buttons.add(e.button())
        self.setFocus()

    @override
    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        self._mouse_buttons.discard(e.button())
        release_pos = e.position().toPoint()

        # Detect click (no drag): if mouse barely moved, treat as a pick
        if self._mouse_press_pos is not None:
            dx = abs(release_pos.x() - self._mouse_press_pos.x())
            dy = abs(release_pos.y() - self._mouse_press_pos.y())
            if dx < 5 and dy < 5:
                if e.button() == QtCore.Qt.MouseButton.LeftButton:
                    self._pick_fixture(release_pos)
                elif e.button() == QtCore.Qt.MouseButton.RightButton:
                    self.deselect_all_requested.emit()

        self._mouse_last_pos = release_pos
        self._mouse_press_pos = None

    @override
    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._mouse_last_pos is None:
            self._mouse_last_pos = e.position().toPoint()
            return
        pos = e.position().toPoint()
        dx = pos.x() - self._mouse_last_pos.x()
        dy = pos.y() - self._mouse_last_pos.y()
        self._mouse_last_pos = pos
        if not self._mouse_buttons:
            return

        # Left-drag: orbit camera (yaw/pitch)
        if QtCore.Qt.MouseButton.LeftButton in self._mouse_buttons:
            self._cam_yaw += dx * 0.3
            self._cam_pitch = max(-89.0, min(89.0, self._cam_pitch - dy * 0.3))
            self.update()

        # Middle/right-drag: pan camera target
        if (QtCore.Qt.MouseButton.MiddleButton in self._mouse_buttons or
                QtCore.Qt.MouseButton.RightButton in self._mouse_buttons):
            ps = float(self._cam_distance) / 800.0
            yaw = math.radians(self._cam_yaw)
            pitch = math.radians(self._cam_pitch)
            cy = math.cos(pitch)
            f = QtGui.QVector3D(float(math.cos(yaw) * cy), float(math.sin(pitch)),
                                float(math.sin(yaw) * cy))
            f.normalize()
            r = QtGui.QVector3D.crossProduct(f, self._camera_up)
            r.normalize()
            u = QtGui.QVector3D.crossProduct(r, f)
            u.normalize()
            self._camera_target += (-r * float(dx) + u * float(dy)) * ps
            self.update()

    @override
    def wheelEvent(self, e: QtGui.QWheelEvent) -> None:
        """Zoom camera in/out via scroll wheel."""
        d = e.angleDelta().y()
        self._cam_distance = max(10.0, min(20000.0, self._cam_distance * (1.0 - d / 1200.0)))
        self.update()

    @override
    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        self._keys_down.add(e.key())
        if e.key() == QtCore.Qt.Key.Key_F:
            self._show_labels = True
            self.update()
        if e.key() == QtCore.Qt.Key.Key_Z:
            self._reset_camera()

    @override
    def keyReleaseEvent(self, e: QtGui.QKeyEvent) -> None:
        self._keys_down.discard(e.key())
        if e.key() == QtCore.Qt.Key.Key_F:
            self._show_labels = False
            self.update()

    # Transform helpers

    def _apply_local_ops(self, matrix: QtGui.QMatrix4x4, ops:
    list[tuple[str, tuple[float, float, float] | tuple[float, float, float, float, float, float]]]) -> None:
        """Apply a sequence of local transform operations to a matrix.

        Supported operations:
            ("translate", (x, y, z))
            ("rotate", (degrees, ax, ay, az, pivot_x, pivot_y, pivot_z))
        """
        for op in ops or ():
            if not op:
                continue
            name, payload = op[0], op[1]
            if name == "translate":
                matrix.translate(*payload)
            elif name == "rotate":
                deg, ax, ay, az, px, py, pz = payload
                matrix.translate(px, py, pz)
                matrix.rotate(deg, ax, ay, az)
                matrix.translate(-px, -py, -pz)

    # Model loading / unloading

    def _ensure_models_loaded(self, obj: StageObject) -> None:
        """Ensure all 3D models for a stage object are uploaded to the GPU."""
        for entry in getattr(obj, "get_model_entries", list)():
            self._ensure_model_loaded_by_path(entry.model_path)

    def _ensure_model_loaded_by_path(self, path: str) -> None:
        """Load and upload a 3D model file if not already cached.

        Supports GLB/glTF (preferred) and OBJ (legacy fallback).
        """
        if not path or path in self._models or path in self._gltf_models:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext in (".glb", ".gltf"):
            try:
                self._gltf_models[path] = _load_gltf_model(path)
                logger.info("Loaded glTF: %s", path)
            except Exception as e:
                logger.error("glTF load error %s: %s", path, e)
            return

        # OBJ fallback loader
        try:
            verts, norms, faces = [], [], []
            with open(path, "r", encoding="UTF-8") as f:
                for line in f:
                    if line.startswith("v "):
                        p = line.split()
                        verts.append((float(p[1]), float(p[2]), float(p[3])))
                    elif line.startswith("vn "):
                        p = line.split()
                        norms.append((float(p[1]), float(p[2]), float(p[3])))
                    elif line.startswith("f "):
                        ps = line.split()[1:]
                        face = []
                        for pt in ps:
                            ii = pt.split("/")
                            face.append((int(ii[0]), int(ii[-1]) if ii[-1] else None))
                        faces.append(face)
            # Build interleaved vertex buffer with index deduplication
            vd, il, im = [], [], {}
            for face in faces:
                if len(face) < 3:
                    continue
                # Fan triangulation for polygons with more than 3 vertices
                for k in range(1, len(face) - 1):
                    for vi, ni in [face[0], face[k], face[k+1]]:
                        key = (vi, ni)
                        if key not in im:
                            p = verts[vi - 1]
                            n = norms[ni - 1] if ni and ni <= len(norms) else (0, 1, 0)
                            im[key] = len(im)
                            vd.extend([p[0], p[1], p[2], n[0], n[1], n[2]])
                        il.append(im[key])
            self._models[path] = _upload_mesh(
                np.array(vd, dtype=np.float32).reshape(-1, 6),
                np.array(il, dtype=np.uint32))
        except Exception as e:
            logger.error("OBJ load error %s: %s", path, e)

    def load_object(self, obj: StageObject) -> None:
        """Public API: ensure models for a newly added object are loaded."""
        self._ensure_models_loaded(obj)

    def _load_all_objects(self) -> None:
        """Reload all objects from stage_config (used after loading a new stage file)."""
        for obj in self._stage_config.objects:
            self._ensure_models_loaded(obj)

    def set_selected_objects(self, object_ids: list[str], is_multi: bool = False) -> None:
        """Set which objects are highlighted in the 3D view.

        Args:
            object_ids: list of object IDs to highlight.
            is_multi: True = orange (multi/group), False = neon-yellow (single).

        """
        self._selected_object_ids = set(object_ids) if object_ids else set()
        self._highlight_is_multi = is_multi

    def remove_object(self, obj: StageObject) -> None:
        """Release GPU resources for models no longer used by any stage object."""
        for entry in getattr(obj, "get_model_entries", list)():
            path = entry.model_path
            if not path:
                continue
            # Check if any remaining object still uses this model
            still_used = any(
                e.model_path == path
                for o in self._stage_config.objects
                for e in getattr(o, "get_model_entries", list)()
            )
            if still_used:
                continue
            # Free GPU resources
            if path in self._models:
                m = self._models.pop(path)
                gl.glDeleteBuffers(1, [m.vbo])
                gl.glDeleteBuffers(1, [m.ebo])
                gl.glDeleteVertexArrays(1, [m.vao])
            if path in self._gltf_models:
                gm = self._gltf_models.pop(path)
                for pl in gm.mesh_primitives.values():
                    for p in pl:
                        gl.glDeleteBuffers(1, [p.vbo])
                        gl.glDeleteBuffers(1, [p.ebo])
                        gl.glDeleteVertexArrays(1, [p.vao])

    # glTF node search

    def _find_gltf_node_world(self, model_path: str, base_model: QtGui.QMatrix4x4, stage_obj: StageObject,
                              target_name: str) -> QtGui.QMatrix4x4 | None:
        """Find a named node in the glTF hierarchy and return its world matrix.

        Uses iterative depth-first search with pan/tilt overrides applied.
        Returns None if the node is not found.
        """
        gm = self._gltf_models.get(model_path)
        if not gm:
            return None
        overrides = self._get_overrides(stage_obj)
        stack = [(int(r), QtGui.QMatrix4x4(base_model)) for r in gm.scene_roots]
        while stack:
            ni, parent = stack.pop()
            if ni < 0 or ni >= len(gm.nodes):
                continue
            node = gm.nodes[ni]
            world = QtGui.QMatrix4x4(parent)
            world *= self._node_local_matrix(node, overrides)
            if node.name == target_name:
                return world
            stack.extend((int(child), world) for child in reversed(node.children or []))
        return None

    def _find_gltf_node_world_rest(self, model_path: str, base_model: QtGui.QMatrix4x4, target_name: str) \
            -> QtGui.QMatrix4x4 | None:
        """Find a named node in the glTF hierarchy and return its world matrix.

        Same as ``_find_gltf_node_world`` but without pan/tilt overrides (rest pose).
        """
        gm = self._gltf_models.get(model_path)
        if not gm:
            return None
        no_overrides = {}
        stack = [(int(r), QtGui.QMatrix4x4(base_model)) for r in gm.scene_roots]
        while stack:
            ni, parent = stack.pop()
            if ni < 0 or ni >= len(gm.nodes):
                continue
            node = gm.nodes[ni]
            world = QtGui.QMatrix4x4(parent)
            world *= self._node_local_matrix(node, no_overrides)
            if node.name == target_name:
                return world
            stack.extend((int(child), world) for child in reversed(node.children or []))
        return None

    # FPS counter overlay

    def _update_fps(self) -> None:
        """Track frames and compute FPS once per second."""
        self._fps_frame_count += 1
        now = time.time()
        elapsed = now - self._fps_last_time
        if elapsed >= 1.0:
            self._fps_display = self._fps_frame_count / elapsed
            self._fps_frame_count = 0
            self._fps_last_time = now

    def _draw_fps_counter(self) -> None:
        """Draw FPS counter text in the bottom-left corner using QPainter."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        text = f"{self._fps_display:.0f} FPS"
        x, y = 10, self.height() - 12

        # Drop shadow for readability
        painter.setPen(QtGui.QColor(0, 0, 0, 180))
        painter.drawText(x + 1, y + 1, text)
        painter.setPen(QtGui.QColor(80, 220, 80))
        painter.drawText(x, y, text)

        painter.end()

    # Fixture name label overlay (F key)

    def _world_to_screen(self, world_pos: QtGui.QVector3D, view_matrix: QtGui.QMatrix4x4) -> QtCore.QPointF:
        """Project a 3D world position to 2D screen coordinates.

        Returns a QPointF, or None if the point is behind the camera.
        """
        mvp = QtGui.QMatrix4x4(self._projection)
        mvp *= view_matrix
        clip = mvp.map(QtGui.QVector4D(
            world_pos.x(), world_pos.y(), world_pos.z(), 1.0))
        if abs(clip.w()) < 1e-6:
            return None
        ndc_x = clip.x() / clip.w()
        ndc_y = clip.y() / clip.w()
        ndc_z = clip.z() / clip.w()
        if ndc_z < -1.0 or ndc_z > 1.0:
            return None
        sx = (ndc_x * 0.5 + 0.5) * self.width()
        sy = (1.0 - (ndc_y * 0.5 + 0.5)) * self.height()
        return QtCore.QPointF(sx, sy)

    def _draw_fixture_labels(self, view_matrix: QtGui.QMatrix4x4) -> None:
        """Draw name labels above each fixture using a QPainter overlay.

        Platform is excluded. Selected fixtures get a highlighted tag color.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        fm = QtGui.QFontMetrics(font)

        for obj in self._stage_config.objects:
            if obj.get_type() == "platform":
                continue

            label = obj.name or obj.get_display_name()
            if not label:
                continue

            # Position label slightly above the fixture
            wx, wy, wz = obj.position
            label_world = QtGui.QVector3D(wx, wy + 25.0, wz)
            screen_pt = self._world_to_screen(label_world, view_matrix)
            if screen_pt is None:
                continue

            # Measure text and compute background rectangle
            text_rect = fm.boundingRect(label)
            pad = 5
            bg_w = text_rect.width() + pad * 2
            bg_h = text_rect.height() + pad * 2
            bg_x = screen_pt.x() - bg_w / 2.0
            bg_y = screen_pt.y() - bg_h
            bg_rect = QtCore.QRectF(bg_x, bg_y, bg_w, bg_h)

            # Style based on selection state
            is_sel = (obj.id in self._selected_object_ids)
            if is_sel:
                if self._highlight_is_multi:
                    painter.setBrush(QtGui.QColor(255, 140, 30, 210))
                    painter.setPen(QtGui.QPen(QtGui.QColor(200, 100, 0), 1.5))
                else:
                    painter.setBrush(QtGui.QColor(230, 220, 20, 210))
                    painter.setPen(QtGui.QPen(QtGui.QColor(180, 170, 0), 1.5))
            else:
                painter.setBrush(QtGui.QColor(30, 30, 40, 190))
                painter.setPen(QtGui.QPen(QtGui.QColor(150, 150, 150), 1))

            painter.drawRoundedRect(bg_rect, 3, 3)

            # Text color: black on bright backgrounds, white on dark
            if is_sel:
                painter.setPen(QtGui.QColor(0, 0, 0))
            else:
                painter.setPen(QtGui.QColor(255, 255, 255))
            painter.drawText(bg_rect, QtCore.Qt.AlignmentFlag.AlignCenter, label)

        painter.end()

    # Camera reset (Z key)

    def _reset_camera(self) -> None:
        """Reset camera to the default stage overview position."""
        self._camera_target = QtGui.QVector3D(0.0, 10.0, 0.0)
        self._cam_yaw = -90.0
        self._cam_pitch = -20.0
        self._cam_distance = (
            QtGui.QVector3D(0.0, 200.0, 400.0) - self._camera_target
        ).length()
        self.update()

    # Click-to-select picking

    def _pick_fixture(self, screen_pos: QPoint) -> None:
        """Find the closest fixture to the click position and emit fixtureClicked.

        Uses simple screen-space distance to each fixture's projected position.
        Closest fixture within a 60px radius is selected.
        """
        self._update_camera_pos()
        view = QtGui.QMatrix4x4()
        view.lookAt(self._camera_pos, self._camera_target, self._camera_up)

        best_id = None
        best_dist = 60.0  # pixel radius threshold

        for obj in self._stage_config.objects:
            if obj.get_type() == "platform":
                continue
            wp = QtGui.QVector3D(obj.position[0], obj.position[1], obj.position[2])
            sp = self._world_to_screen(wp, view)
            if sp is None:
                continue
            dx = sp.x() - screen_pos.x()
            dy = sp.y() - screen_pos.y()
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_id = obj.id

        if best_id:
            self.fixture_clicked.emit(best_id)
