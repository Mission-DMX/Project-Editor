"""3D OpenGL viewport for the stage visualizer.

Renders the scene in three passes (shadow maps, scene objects, volumetric
beam cones) and handles camera, picking and the name-label overlay.

"""

from __future__ import annotations

import ctypes
import math
import os
import time
from curses import has_key
from logging import getLogger
from typing import TYPE_CHECKING, override

import numpy as np
from OpenGL import GL as gl  # NOQA: N811 it is common practice to import is as lower case gl. Also it's not a const.
from PySide6 import QtCore, QtGui
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from model.visualizer.stage.so_moving_head import MovingHead
from utility import resource_path
from view.gl import _apply_local_ops
from view.gl.gltf_model import GltfModel, GltfNode
from view.gl.model_3d import Model3D
from view.gl.shaders import delete_shader, load_and_link_shader_from_files
from view.visualizer.geometry_helpers import (
    MAX_SHADOW_MAPS,
    MAX_SPOT_LIGHTS,
    SHADOW_MAP_SIZE,
    build_base_model_matrix,
    build_cone_matrix,
    compute_light_space_matrix,
    create_ground_plane,
    create_unit_cone,
    get_overrides,
    node_local_matrix,
)
from view.visualizer.spotlight_data import SpotLightData

if TYPE_CHECKING:
    from collections.abc import Sequence

    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication, QWidget

    from model.visualizer.stage.stage_config import StageConfig, StageObject

logger = getLogger(__name__)


class Stage3DWidget(QOpenGLWidget):
    """OpenGL 3D viewport for the stage visualizer."""

    # Emitted when user left-clicks a fixture in 3D
    fixture_clicked = QtCore.Signal(str)
    # Emitted when user right-clicks (deselect all)
    deselect_all_requested = QtCore.Signal()

    def __init__(self, stage_config: StageConfig, parent: QWidget | None=None) -> None:
        """Initialize using given stage configuration and parent."""
        super().__init__(parent)
        self._gl_initialized = False
        self._stage_config = stage_config

        # Shader programs (initialized in initializeGL)
        self._scene_program: int = 0
        self._beam_program: int = 0
        self._depth_program: int = 0
        self._lense_light_program: int = 0

        # Uniform location caches
        self._scene_uniforms = {}             # scene shader uniforms
        self._sc_light_locs = []  # per-light uniform locations
        self._beam_uniforms = {}             # beam shader uniforms
        self._depth_uniforms = {}             # depth shader uniforms

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

        # base quad
        self._lense_light_quad_model: Model3D | None = None
        self._lense_light_instance_vbo: int = 0
        self._lense_light_data: np.ndarray = np.zeros(16, dtype=np.float32)
        self._lense_light_data_last_buffer_size: int = 0
        self._lense_shader_view_uniform_location: gl.GL_INT = 0
        self._lense_shader_proj_uniform_location: gl.GL_INT = 0

    # OpenGL initialization

    @override
    def initializeGL(self) -> None:
        fmt = self.context().format()
        logger.error(
            "Initializing Visualizer OpenGL context with version %d.%d, profile=%s, options=%s\nGL_VENDOR: %s\n"
            "GL_RENDERER: %s\nGL_VERSION: %s",
            fmt.majorVersion(),
            fmt.minorVersion(),
            fmt.profile(),
            fmt.options(),
            gl.glGetString(gl.GL_VENDOR).decode(),
            gl.glGetString(gl.GL_RENDERER).decode(),
            gl.glGetString(gl.GL_VERSION).decode()
        )

        gl.glClearColor(0.02, 0.02, 0.03, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)

        # Compile and link shader programs
        try:
            self._scene_program = load_and_link_shader_from_files(
                resource_path(os.path.join("resources", "shaders", "stage_scene.vert")),
                resource_path(os.path.join("resources", "shaders", "stage_scene.frag"))
            )
        except RuntimeError as e:
            logger.error("Scene shader: %s", e)
            return
        try:
            self._beam_program = load_and_link_shader_from_files(
                resource_path(os.path.join("resources", "shaders", "stage_beam.vert")),
                resource_path(os.path.join("resources", "shaders", "stage_beam.frag"))
            )
        except RuntimeError as e:
            logger.error("Beam shader: %s", e)
        try:
            self._depth_program = load_and_link_shader_from_files(
                resource_path(os.path.join("resources", "shaders", "stage_depth.vert")),
                resource_path(os.path.join("resources", "shaders", "stage_depth.frag")))
        except RuntimeError as e:
            logger.error("Depth shader: %s", e)

        try:
            self._lense_light_program = load_and_link_shader_from_files(
                resource_path(os.path.join("resources", "shaders", "stage_lense.vert")),
                resource_path(os.path.join("resources", "shaders", "stage_lense.frag"))
            )
        except RuntimeError as e:
            logger.error("Lense shader: %s", e)

        # Cache uniform locations for each program

        # Scene shader
        sp = self._scene_program
        for name in ("projection", "view", "model", "viewPos", "baseColor",
                      "ambientLevel", "numLights", "numShadowLights", "shadowMap",
                      "highlightMix", "highlightColor"):
            self._scene_uniforms[name] = gl.glGetUniformLocation(sp, name)

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
                self._beam_uniforms[name] = gl.glGetUniformLocation(bp, name)

        # Depth shader
        dp = self._depth_program
        if dp:
            self._depth_uniforms["lightSpaceMatrix"] = gl.glGetUniformLocation(dp, "lightSpaceMatrix")
            self._depth_uniforms["model"] = gl.glGetUniformLocation(dp, "model")

        # Create shadow map resources
        self._init_shadow_map_resources()

        # Create geometry
        self._beam_cone = create_unit_cone(64, context=self.context())
        self._ground_plane = create_ground_plane(2000.0, context=self.context())

        # Load 3D models for all existing stage objects
        for obj in self._stage_config.objects:
            self._ensure_models_loaded(obj)

        # x y U V
        self._lense_light_quad_model = Model3D.upload_vao(np.array([
                -1.0, -1.0, 0.0, 0.0,
                1.0, -1.0, 1.0, 0.0,
                1.0, 1.0, 1.0, 1.0,
                -1.0, 1.0, 0.0, 1.0
            ], dtype=np.float32), np.array([0, 1, 2, 2, 3, 0], dtype=np.int32), self.context(),
            stride=4, vertex_size=2, vertex_location_index=4, uv_location_index=5
        )
        gl.glBindVertexArray(self._lense_light_quad_model.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._lense_light_quad_model.vbo)

        # 0 Position
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 16*4, ctypes.c_void_p(0))
        gl.glVertexAttribDivisor(0, 1)

        # 1 Direction
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 16*4, ctypes.c_void_p(4*4))
        gl.glVertexAttribDivisor(1, 1)

        # 2 Size
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(2, 1, gl.GL_FLOAT, gl.GL_FALSE, 16*4, ctypes.c_void_p(8*4))
        gl.glVertexAttribDivisor(2, 1)

        # 3 Color
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribPointer(3, 4, gl.GL_FLOAT, gl.GL_FALSE, 16*4, ctypes.c_void_p(12*4))
        gl.glVertexAttribDivisor(3, 1)

        self._lense_shader_view_uniform_location = gl.glGetUniformLocation(self._lense_light_program, "uView")
        self._lense_shader_proj_uniform_location = gl.glGetUniformLocation(self._lense_light_program, "uProj")

        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

        self.context().aboutToBeDestroyed.connect(self._clean_up_opengl_context)
        logger.info("OpenGL init done. %d objects.", len(self._stage_config.objects))
        self._gl_initialized = True

    @property
    def gl_initialized(self) -> bool:
        """Check if the OpenGL context was already initialized."""
        return self._gl_initialized

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

        proj_data = np.array(self._projection.copyDataTo(), dtype=np.float32)
        view_data = np.array(view.copyDataTo(), dtype=np.float32)

        spotlights, beam_list = self._collect_lights_and_beams()
        lense_light_count = self._collect_lense_lights()

        # PASS 0: Shadow maps
        light_space_matrices = self._render_shadow_maps(spotlights)

        # Restore widget's default FBO and viewport
        default_fbo = self.defaultFramebufferObject()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, default_fbo)
        gl.glViewport(0, 0, self.width(), self.height())
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # PASS 1.1: lense_lights
        self._render_lense_lights(lense_light_count, proj_data, view_data)

        # PASS 1: Scene objects (Phong + spotlights + shadows)
        gl.glUseProgram(self._scene_program)
        gl.glUniformMatrix4fv(self._scene_uniforms["projection"], 1, gl.GL_TRUE, proj_data)
        gl.glUniformMatrix4fv(self._scene_uniforms["view"], 1, gl.GL_TRUE, view_data)
        cam = self._camera_pos
        gl.glUniform3f(self._scene_uniforms["viewPos"], cam.x(), cam.y(), cam.z())
        gl.glUniform1f(self._scene_uniforms["ambientLevel"], 0.09)

        # Upload spotlight data to shader
        num_lights = min(len(spotlights), MAX_SPOT_LIGHTS)
        gl.glUniform1i(self._scene_uniforms["numLights"], num_lights)
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
        gl.glUniform1i(self._scene_uniforms["numShadowLights"], num_shadow)
        for i, lsm in enumerate(light_space_matrices):
            gl.glUniformMatrix4fv(self._sc_lsm_locs[i], 1, gl.GL_TRUE, lsm.copyDataTo())

        # Bind shadow map texture array to texture unit 0
        gl.glActiveTexture(gl.GL_TEXTURE0)
        if self._shadow_tex is not None:
            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._shadow_tex)
        gl.glUniform1i(self._scene_uniforms["shadowMap"], 0)

        # Draw ground plane
        if self._ground_plane:
            gl.glUniformMatrix4fv(self._scene_uniforms["model"], 1, gl.GL_TRUE, QtGui.QMatrix4x4().copyDataTo())
            gl.glUniform3f(self._scene_uniforms["baseColor"], 0.15, 0.15, 0.15)
            gl.glUniform1f(self._scene_uniforms["highlightMix"], 0.0)
            gl.glBindVertexArray(self._ground_plane.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, self._ground_plane.index_count, gl.GL_UNSIGNED_INT, None)

        # Draw stage objects with selection highlighting
        hl_color = (1.0, 0.55, 0.1) if self._highlight_is_multi else (1.0, 0.95, 0.15)
        # warm orange for multi/group else neon yellow for single
        gl.glUniform3f(self._scene_uniforms["highlightColor"], *hl_color)

        for idx, obj in enumerate(self._stage_config.objects):
            is_selected = (obj.id in self._selected_object_ids)
            # Alternate object colors for visual distinction
            color = (0.50, 0.50, 0.55) if idx % 2 == 0 else (0.45, 0.45, 0.50)
            gl.glUniform1f(self._scene_uniforms["highlightMix"], 1.0 if is_selected else 0.0)
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
            lsm = compute_light_space_matrix(sl)
            light_space_matrices.append(lsm)

            # Attach this layer of the texture array to the FBO
            gl.glFramebufferTextureLayer(
                gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT,
                self._shadow_tex, 0, i
            )
            gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

            gl.glUniformMatrix4fv(self._depth_uniforms["lightSpaceMatrix"], 1, gl.GL_TRUE, lsm.copyDataTo())
            self._draw_scene_depth_only()

        gl.glDisable(gl.GL_POLYGON_OFFSET_FILL)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glUseProgram(0)

        return light_space_matrices

    def _draw_scene_depth_only(self) -> None:
        """Draw all scene objects with the depth shader (for shadow maps)."""
        for obj in self._stage_config.objects:
            base = build_base_model_matrix(obj)
            for entry in getattr(obj, "get_model_entries", list)():
                model = QtGui.QMatrix4x4(base)
                _apply_local_ops(model, getattr(entry, "local_ops", ()))

                if entry.model_path in self._gltf_models:
                    self._traverse_gltf(entry.model_path, model, obj,
                                        model_loc=self._depth_uniforms["model"])
                elif entry.model_path in self._models:
                    gl.glUniformMatrix4fv(self._depth_uniforms["model"], 1, gl.GL_TRUE, model.copyDataTo())
                    m = self._models[entry.model_path]
                    gl.glBindVertexArray(m.vao)
                    gl.glDrawElements(gl.GL_TRIANGLES, m.index_count, gl.GL_UNSIGNED_INT, None)

        gl.glBindVertexArray(0)

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
        overrides = get_overrides(stage_obj)

        # Stack of (node_index, parent_world_matrix)
        stack = [(int(r), QtGui.QMatrix4x4(base_model)) for r in gm.scene_roots]
        while stack:
            ni, parent = stack.pop()
            if ni < 0 or ni >= len(gm.nodes):
                continue
            node = gm.nodes[ni]
            world = QtGui.QMatrix4x4(parent)
            world *= node_local_matrix(node, overrides)

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
        base = build_base_model_matrix(obj)
        gl.glUniform3f(self._scene_uniforms["baseColor"], color[0], color[1], color[2])

        for entry in getattr(obj, "get_model_entries", list)():
            model = QtGui.QMatrix4x4(base)
            _apply_local_ops(model, getattr(entry, "local_ops", ()))

            if entry.model_path in self._gltf_models:
                self._traverse_gltf(entry.model_path, model, obj,
                                    model_loc=self._scene_uniforms["model"],
                                    color=color, color_loc=self._scene_uniforms["baseColor"])
            elif entry.model_path in self._models:
                gl.glUniformMatrix4fv(self._scene_uniforms["model"], 1, gl.GL_TRUE, model.copyDataTo())
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
        gl.glUniformMatrix4fv(self._beam_uniforms["projection"], 1, gl.GL_TRUE, proj_data)
        gl.glUniformMatrix4fv(self._beam_uniforms["view"], 1, gl.GL_TRUE, view_data)

        # Bind shadow map to texture unit 1 (unit 0 is used by the scene pass)
        has_shadow = (self._shadow_tex is not None and len(light_space_matrices) > 0)
        if has_shadow:
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._shadow_tex)
            gl.glUniform1i(self._beam_uniforms["shadowMap"], 1)

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

            mat = build_cone_matrix(origin, direction, actual_length, actual_radius)
            gl.glUniformMatrix4fv(self._beam_uniforms["model"], 1, gl.GL_TRUE, mat.copyDataTo())
            gl.glUniform3f(self._beam_uniforms["beamColor"], color[0], color[1], color[2])

            # Upload per-beam shadow data
            shadow_layer = beam_idx
            if has_shadow and shadow_layer < len(light_space_matrices):
                gl.glUniform1i(self._beam_uniforms["hasShadow"], 1)
                gl.glUniform1i(self._beam_uniforms["beamShadowLayer"], shadow_layer)
                gl.glUniformMatrix4fv(
                    self._beam_uniforms["beamLightSpaceMatrix"], 1, gl.GL_TRUE,
                    light_space_matrices[shadow_layer].copyDataTo())
            else:
                gl.glUniform1i(self._beam_uniforms["hasShadow"], 0)

            # Light origin for the volumetric shadow ray-march.
            gl.glUniform3f(self._beam_uniforms["beamLightPos"],
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
        gl.glUseProgram(0)

    def _render_lense_lights(self, light_data_count: int, proj_data: Sequence[float],
                             view_data: Sequence[float]) -> None:
        gl.glUseProgram(self._lense_light_program)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._lense_light_quad_model.vbo)
        buffer_size = self._lense_light_data.nbytes
        if buffer_size != self._lense_light_data_last_buffer_size:
            gl.glBufferData(gl.GL_ARRAY_BUFFER, buffer_size, self._lense_light_data, gl.GL_DYNAMIC_DRAW)
            self._lense_light_data_last_buffer_size = buffer_size
        else:
            gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, buffer_size, self._lense_light_data)
        gl.glUniformMatrix4fv(self._lense_shader_proj_uniform_location, 1, gl.GL_FALSE, proj_data)
        gl.glUniformMatrix4fv(self._lense_shader_view_uniform_location, 1, gl.GL_FALSE, view_data)
        gl.glBindVertexArray(self._lense_light_quad_model.vao)
        gl.glDrawElementsInstanced(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, ctypes.c_void_p(0), light_data_count)
        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDisable(gl.GL_BLEND)
        gl.glUseProgram(0)

    # Light and beam collection

    def _collect_lense_lights(self) -> int:
        """Compute the positions of lense lights.

        Updates:
            List of lense lights. Each tuple contains the effective position (3), effective rotation (3), size (1) and
            RGB color in range 0 to 1 (3).

        Returns:
            Number of lense lights.

        """
        lense_lights_count = 0
        stage_objects: list[StageObject] = getattr(self._stage_config, "objects", [])
        arr = self._lense_light_data
        for obj in stage_objects:
            lense_lights: list[tuple[QtGui.QVector3D, QtGui.QVector3D, float,
            tuple[int, int, int], str, str]] | None = getattr(obj, "lense_colors", None)
            if lense_lights is None:
                continue
            for ll_definition in lense_lights:
                if arr.shape[0] < (lense_lights_count + 1) * 16:
                    self._lense_light_data = np.resize(arr, (lense_lights_count + 1) * 16)
                    arr = self._lense_light_data
                position_offset_from_base_node: QtGui.QVector3D = ll_definition[0]
                rotation_offset_from_base_node: QtGui.QVector3D = ll_definition[1]
                size: float = ll_definition[2]
                color: tuple[int, int, int] = ll_definition[3]
                position, direction = self._calculate_extension_translation_matrices(
                    obj,
                    obj.model_path,  # model path
                    ll_definition[4],  # origin node name
                    ll_definition[5]   # name of movable node
                )
                position += position_offset_from_base_node
                direction += rotation_offset_from_base_node
                arr[16*lense_lights_count + 0] = position.x()
                arr[16*lense_lights_count + 1] = position.y()
                arr[16*lense_lights_count + 2] = position.z()
                arr[16*lense_lights_count + 4] = direction.x()
                arr[16*lense_lights_count + 5] = direction.y()
                arr[16*lense_lights_count + 6] = direction.z()
                arr[16*lense_lights_count + 8] = size
                arr[16*lense_lights_count + 12] = color[0] / 255.0  # r
                arr[16*lense_lights_count + 13] = color[1] / 255.0  # g
                arr[16*lense_lights_count + 14] = color[2] / 255.0  # b
                arr[16*lense_lights_count + 15] = 1.0  # a
                lense_lights_count += 1
        return lense_lights_count

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
            beam_origin_node_name = MovingHead.BEAM_ORIGIN_NODE_NAME
            tilt_node_name = MovingHead.TILT_NODE_NAME
        except Exception:
            logger.error("Bug: Object did not provide beam origin node and tilt node.")
            beam_origin_node_name = "BeamOrigin"
            tilt_node_name = "Cylinder.018"

        stage_objects: list[StageObject] = getattr(self._stage_config, "objects", [])
        for obj in stage_objects:
            has_beam = hasattr(obj, "beam_on")
            if not has_beam or not bool(getattr(obj, "beam_on", False)):
                continue

            entries = getattr(obj, "get_model_entries", list)()
            if not entries:
                continue
            model_path = entries[0].model_path

            origin_pos, dir_vec = self._calculate_extension_translation_matrices(
                obj, model_path, beam_origin_node_name, tilt_node_name
            )

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

    def _calculate_extension_translation_matrices(self, obj: StageObject, model_path: str | None,
                                                  origin_node_name: str | None,
                                                  tilt_node_name: str | None) -> (
            tuple)[QtGui.QVector3D, QtGui.QVector3D]:
        """Calculate end-effector position and direction from stage object and optional transition nodes."""
        base = build_base_model_matrix(obj)
        has_pan_and_tilt = hasattr(obj, "pan") and hasattr(obj, "tilt")
        has_trans_node_data = tilt_node_name is not None and model_path is not None and origin_node_name is not None
        if has_pan_and_tilt and has_trans_node_data:
            # Find world-space position of the BeamOrigin node
            origin_mat = self._find_gltf_node_world(model_path, base, obj, origin_node_name)
            if origin_mat is None:
                origin_mat = QtGui.QMatrix4x4(base)
            origin_pos = origin_mat.map(QtGui.QVector3D(0.0, 0.0, 0.0))

            # Find world-space position of the tilt pivot node
            tilt_mat = self._find_gltf_node_world(model_path, base, obj, tilt_node_name)
        else:
            origin_pos = QtGui.QVector3D(*obj.position)
            degrees = np.degrees(np.array(obj.rotation, dtype=np.float64))
            tilt_mat = QtGui.QMatrix4x4().rotate(QtGui.QQuaternion.fromEulerAngles(*degrees))

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
            dir_vec = QtGui.QVector3D(0.0, 1.0, 0.0)
        return origin_pos, dir_vec

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

    def _ensure_models_loaded(self, obj: StageObject) -> None:
        """Ensure all 3D models for a stage object are uploaded to the GPU."""
        for entry in getattr(obj, "get_model_entries", list)():
            self._ensure_model_loaded_by_path(entry.model_path)

    def _ensure_model_loaded_by_path(self, path: str) -> None:
        """Load and upload a 3D model file if not already cached.

        Supports GLB/glTF (preferred) and OBJ (legacy fallback).
        """
        self.makeCurrent()
        if not path or path in self._models or path in self._gltf_models:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext in (".glb", ".gltf"):
            try:
                self._gltf_models[path] = GltfModel.load_gltf_model(path, self.context())
                logger.debug("Loaded glTF: %s", path)
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
            self._models[path] = Model3D.upload_mesh(
                np.array(vd, dtype=np.float32).reshape(-1, 6),
                np.array(il, dtype=np.uint32),
                context=self.context()
            )
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
                m.unload()
            if path in self._gltf_models:
                gm = self._gltf_models.pop(path)
                gm.unload()

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
        overrides = get_overrides(stage_obj)
        stack = [(int(r), QtGui.QMatrix4x4(base_model)) for r in gm.scene_roots]
        while stack:
            node_index, parent = stack.pop()
            if node_index < 0 or node_index >= len(gm.nodes):
                continue
            node = gm.nodes[node_index]
            world = QtGui.QMatrix4x4(parent)
            world *= node_local_matrix(node, overrides)
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
            world *= node_local_matrix(node, no_overrides)
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

    def _world_to_screen(self, world_pos: QtGui.QVector3D, view_matrix: QtGui.QMatrix4x4) -> QtCore.QPointF | None:
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

    def _clean_up_opengl_context(self) -> None:
        """Unload the models."""
        for model in self._models.values():
            model.unload()
        for model in self._gltf_models.values():
            model.unload()
        if self._lense_light_quad_model is not None:
            self._lense_light_quad_model.unload()
        delete_shader(self._lense_light_program)
        self._lense_light_program = 0
        delete_shader(self._beam_program)
        self._beam_program = 0
        delete_shader(self._depth_program)
        self._depth_program = 0
        delete_shader(self._scene_program)
        self._scene_program = 0
        logger.debug("Successfully cleaned up models.")
