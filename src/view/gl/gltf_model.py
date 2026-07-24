"""Contains gltf model handling."""

from __future__ import annotations

import json
import struct
from typing import Any

import numpy as np

from view.gl.model_3d import Model3D

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

    def __init__(self, nodes: list[GltfNode], scene_roots: list[int],
                 mesh_primitives: dict[int, list[Model3D]]) -> None:
        """Initialize the struct."""
        self.nodes: list[GltfNode] = nodes                    # list of GltfNode
        self.scene_roots: list[int] = scene_roots        # list of root node indices
        self.mesh_primitives: dict[int, list[Model3D]] = mesh_primitives  # dict: mesh_index -> [Model3D]


    @classmethod
    def load_gltf_model(cls, path: str) -> GltfModel:
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
                plist.append(Model3D.upload_mesh(np.concatenate([pos[:, :3], nrm[:, :3]], axis=1), idx))
            if plist:
                mesh_prims[mi] = plist

        return cls(nodes, scene_roots, mesh_prims)


# glTF binary loading
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
