"""Contains file system paths for data."""

from __future__ import annotations

import os

from utility import resource_path

# Bundled GLB models. Keys must match StageObject.get_type().
DEFAULT_MODEL_PATHS: dict[str, str] = {
    "truss":               resource_path(os.path.join("resources", "3dmodels", "truss.glb")),
    "truss_default":       resource_path(os.path.join("resources", "3dmodels", "truss.glb")),
    "truss_2point_medium": resource_path(os.path.join("resources", "3dmodels", "truss 2point medium.glb")),
    "truss_cross":         resource_path(os.path.join("resources", "3dmodels", "truss cross.glb")),
    "truss_long":          resource_path(os.path.join("resources", "3dmodels", "truss long.glb")),
    "truss_medium":        resource_path(os.path.join("resources", "3dmodels", "truss medium.glb")),
    "platform":            resource_path(os.path.join("resources", "3dmodels", "platform.glb")),
    "moving_head":         resource_path(os.path.join("resources", "3dmodels", "movinghead.glb")),
}

# User-local stage directory (XDG).
STAGE_DIR = os.path.join(
    os.path.expanduser("~"), ".local", "share", "missionDMX", "stage"
)
if not os.path.exists(STAGE_DIR):
    os.makedirs(STAGE_DIR)
DEFAULT_STAGE_PATH = os.path.join(STAGE_DIR, "current_stage.yaml")
