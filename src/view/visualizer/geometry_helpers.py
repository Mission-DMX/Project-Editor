"""Contains various rendering and geometry helper methods."""

from __future__ import annotations

import math
from logging import getLogger
from typing import TYPE_CHECKING

import numpy as np
from PySide6 import QtGui

from view.gl.model_3d import Model3D

if TYPE_CHECKING:
    from PySide6.QtGui import QOpenGLContext

    from model.visualizer.stage.stage_object import StageObject
    from view.gl.gltf_model import GltfNode
    from view.visualizer.spotlight_data import SpotLightData

logger = getLogger(__name__)

# also needs to be updated in stage_scene.frag
MAX_SPOT_LIGHTS = 16    # maximum simultaneous spotlights in the scene shader,

# also needs to be updated in stage_scene.frag
MAX_SHADOW_MAPS = 4     # shadow-casting lights (texture array layers),
SHADOW_MAP_SIZE = 1024  # per-layer shadow map resolution


def build_cone_matrix(origin: QtGui.QVector3D, direction: QtGui.QVector3D,
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


def node_local_matrix(node: GltfNode,
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


def get_overrides(stage_obj: StageObject) -> dict[str, tuple[float, float, float, float]]:
    """Get glTF node rotation overrides (pan/tilt) from a stage object."""
    if stage_obj and hasattr(stage_obj, "get_gltf_node_overrides"):
        try:
            return stage_obj.get_gltf_node_overrides() or {}
        except Exception as e:
            logger.exception("Unable to extract GLTF overrides from model (%s) : %s", str(stage_obj), str(e))
    return {}


def build_base_model_matrix(obj: StageObject) -> QtGui.QMatrix4x4:
    """Build the T * Rz * Ry * Rx * S model matrix for a stage object."""
    m = QtGui.QMatrix4x4()
    m.translate(obj.position[0], obj.position[1], obj.position[2])
    m.rotate(obj.rotation[2], 0.0, 0.0, 1.0)
    m.rotate(obj.rotation[1], 0.0, 1.0, 0.0)
    m.rotate(obj.rotation[0], 1.0, 0.0, 0.0)
    m.scale(float(getattr(obj, "scale", 1.0)))
    return m


def compute_light_space_matrix(spotlight: SpotLightData) -> QtGui.QMatrix4x4:
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


def create_unit_cone(segments: int=48, context: QOpenGLContext | None = None) -> Model3D:
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
    return Model3D.upload_vao(v, ii, context)


def create_ground_plane(size: float=2000.0, context: QOpenGLContext | None = None) -> Model3D:
    """Create a flat ground plane quad at y=0 with upward normals."""
    h = size / 2.0
    v = np.array([
        -h, 0, -h, 0, 1, 0,  h, 0, -h, 0, 1, 0,
         h, 0,  h, 0, 1, 0, -h, 0,  h, 0, 1, 0,
    ], dtype=np.float32)
    ii = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    return Model3D.upload_vao(v, ii, context)
