"""Stage configuration: data model, YAML persistence and fixture classes.

Objects on the stage are subclasses of ``StageObject`` (Truss, MovingHead,
Platform). ``StageConfig`` is the aggregate root that loads and saves
the full stage to a YAML file under ``~/.local/share/missionDMX/stage/``.
"""

import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ruamel import yaml

from utility import resource_path

logger = logging.getLogger(__file__)

# User-local stage directory (XDG).
STAGE_DIR = os.path.join(
    os.path.expanduser("~"), ".local", "share", "missionDMX", "stage"
)
DEFAULT_STAGE_PATH = os.path.join(STAGE_DIR, "current_stage.yaml")


def get_default_stage_path() -> str:
    """Return the persistent stage file path, creating it on first run."""
    os.makedirs(STAGE_DIR, exist_ok=True)
    if not os.path.exists(DEFAULT_STAGE_PATH):
        bundled = resource_path(os.path.join("resources", "data", "stage.yaml"))
        if os.path.exists(bundled):
            shutil.copy2(bundled, DEFAULT_STAGE_PATH)
            logger.info("Copied bundled stage.yaml to %s", DEFAULT_STAGE_PATH)
    return DEFAULT_STAGE_PATH


def backup_stage_file(stage_path: str) -> str:
    """Write a timestamped copy next to the stage file; return its path."""
    if not os.path.exists(stage_path):
        return ""
    directory = os.path.dirname(stage_path)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(directory, f"stage_backup_{timestamp}.yaml")
    shutil.copy2(stage_path, backup_path)
    logger.info("Stage backup created: %s", backup_path)
    return backup_path


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


@dataclass(frozen=True)
class ModelEntry:
    """One mesh to render for a stage object, with optional local transforms.

    ``local_ops`` entries are applied before the object's world transform
    and take the form ``("translate", (x, y, z))`` or
    ``("rotate", (degrees, ax, ay, az), pivot=(px, py, pz))``.
    """

    model_path: str
    local_ops: tuple[tuple[str, Any], ...] = ()


class StageObject:
    """Base class for anything placed on the stage."""

    def __init__(
        self,
        object_id: str,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        scale: float | None = None,
        model_path: str | None = None,
    ):
        self.id = object_id
        self.name = ""
        self.position = position if position is not None else (0.0, 0.0, 0.0)
        self.rotation = rotation if rotation is not None else (0.0, 0.0, 0.0)
        self.scale = float(scale) if scale is not None else 1.0
        self.model_path = model_path

        # Optional link to a real DMX device (universe, start_channel, mapping).
        self.device_config: dict[str, Any] | None = None

        if self.model_path is None:
            key = self.get_type().lower()
            if key in DEFAULT_MODEL_PATHS:
                self.model_path = DEFAULT_MODEL_PATHS[key]

    def get_type(self) -> str:
        return "default"

    def get_display_name(self) -> str:
        return self.get_type()

    def get_model_entries(self) -> list[ModelEntry]:
        """One or more render entries. Composite fixtures override this."""
        if not self.model_path:
            return []
        return [ModelEntry(self.model_path)]

    def to_dict(self) -> dict[str, Any]:
        d = {
            "id": self.id,
            "name": self.name,
            "type": self.get_type(),
            "position": {"x": self.position[0], "y": self.position[1], "z": self.position[2]},
            "rotation": {"x": self.rotation[0], "y": self.rotation[1], "z": self.rotation[2]},
            "scale": self.scale,
        }
        if self.device_config:
            d["device"] = self.device_config
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        object_id = data.get("id")
        pos = data.get("position", {})
        rot = data.get("rotation", {})
        position = (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0))
        rotation = (rot.get("x", 0.0), rot.get("y", 0.0), rot.get("z", 0.0))
        scale = float(data.get("scale", 1.0))
        obj = cls(object_id, position, rotation, scale)
        obj.name = data.get("name", "")
        obj.device_config = data.get("device")
        return obj


class Platform(StageObject):
    """Static stage floor. Every stage has exactly one."""

    DEFAULT_POSITION = (-23.0, 0.0, 0.0)

    def __init__(self, object_id: str = "platform", position=None,
                 rotation=None, scale: float = 1.0):
        super().__init__(
            object_id,
            position if position is not None else Platform.DEFAULT_POSITION,
            rotation if rotation is not None else (0.0, 0.0, 0.0),
            float(scale),
            model_path=DEFAULT_MODEL_PATHS["platform"],
        )

    def get_type(self) -> str:
        return "platform"

    def get_display_name(self) -> str:
        return "Platform"


class Truss(StageObject):
    """Truss fixture (default, cross, long, medium, 2-point)."""

    def __init__(self, object_id: str, variant: str = "default",
                 position=None, rotation=None, scale: float = 1.0):
        self.variant = variant

        key = f"truss_{variant}" if variant != "" else "truss"
        if key not in DEFAULT_MODEL_PATHS:
            key = "truss_default"
            self.variant = "default"

        super().__init__(
            object_id, position, rotation, float(scale),
            model_path=DEFAULT_MODEL_PATHS[key],
        )

    def get_type(self) -> str:
        return f"truss_{self.variant}" if self.variant != "" else "truss"

    def get_display_name(self) -> str:
        mapping = {
            "default": "Truss Default",
            "2point_medium": "Truss 2-Point",
            "cross": "Truss Cross",
            "long": "Truss Long",
            "medium": "Truss Medium",
        }
        return mapping.get(self.variant, f"Truss {self.variant}")

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["variant"] = self.variant
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        object_id = data.get("id")
        pos = data.get("position", {})
        rot = data.get("rotation", {})
        position = (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0))
        rotation = (rot.get("x", 0.0), rot.get("y", 0.0), rot.get("z", 0.0))

        # Variant may be explicit or embedded in legacy type strings like "truss_cross".
        t = (data.get("type") or "truss").lower()
        variant = data.get("variant")
        if not variant:
            if t == "truss":
                variant = "default"
            elif t.startswith("truss_"):
                variant = t[len("truss_"):]
            else:
                variant = "default"

        scale = float(data.get("scale", 1.0))
        obj = cls(object_id, variant=variant, position=position,
                  rotation=rotation, scale=scale)
        obj.name = data.get("name", "")
        obj.device_config = data.get("device")
        return obj


class MovingHead(StageObject):
    """Moving head with pan/tilt control and colored beam.

    Loaded from a single .glb file whose node hierarchy the renderer
    overrides per frame using the axis-angle pairs from
    ``get_gltf_node_overrides()``.
    """

    # Names of the joint nodes inside the .glb model.
    PAN_NODE_NAME = "Cube.035"
    TILT_NODE_NAME = "Cylinder.018"
    BEAM_ORIGIN_NODE_NAME = "BeamOrigin"

    PAN_AXIS = (0.0, 1.0, 0.0)
    TILT_AXIS = (1.0, 0.0, 0.0)

    def __init__(
        self,
        object_id: str,
        channels: int = 16,
        position=None,
        rotation=None,
        scale: float = 20.0,   # .glb is small; scale up for visibility
        pan: float = 0.0,
        tilt: float = 0.0,
        beam_on: bool = True,
        beam_color: tuple[int, int, int] | None = None,
        dimmer: float = 1.0,
    ):
        # Must be set before super().__init__ since get_type() reads it.
        self.channels = 8 if int(channels) == 8 else 16
        super().__init__(object_id, position, rotation, float(scale), model_path=None)

        self.pan = float(pan)
        self.tilt = float(tilt)
        self.beam_on = bool(beam_on)

        if beam_color is None:
            beam_color = (0, 255, 0)
        r, g, b = beam_color
        self.beam_color = (int(r), int(g), int(b))
        self.dimmer = max(0.0, min(1.0, float(dimmer)))

    def get_type(self) -> str:
        return "moving_head"

    def get_display_name(self) -> str:
        return "Moving Head"

    def get_model_entries(self) -> list[ModelEntry]:
        return [ModelEntry(DEFAULT_MODEL_PATHS["moving_head"])]

    def get_gltf_node_overrides(self) -> dict[str, tuple[float, float, float, float]]:
        """Axis-angle overrides for pan and tilt: ``{node: (ax, ay, az, deg)}``."""
        return {
            MovingHead.PAN_NODE_NAME:  (*MovingHead.PAN_AXIS, float(self.pan)),
            MovingHead.TILT_NODE_NAME: (*MovingHead.TILT_AXIS, float(self.tilt)),
        }

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "pan": self.pan,
            "tilt": self.tilt,
            "channels": self.channels,
            "beam_on": bool(self.beam_on),
            "beam_color": {
                "r": int(self.beam_color[0]),
                "g": int(self.beam_color[1]),
                "b": int(self.beam_color[2]),
            },
            "dimmer": float(self.dimmer),
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        object_id = data.get("id")
        pos = data.get("position", {})
        rot = data.get("rotation", {})
        position = (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0))
        rotation = (rot.get("x", 0.0), rot.get("y", 0.0), rot.get("z", 0.0))
        pan = float(data.get("pan", 0.0))
        tilt = float(data.get("tilt", 0.0))
        beam_on = bool(data.get("beam_on", True))

        bc = data.get("beam_color") or {}
        if isinstance(bc, dict):
            beam_color = (int(bc.get("r", 0)), int(bc.get("g", 255)), int(bc.get("b", 0)))
        elif isinstance(bc, (list, tuple)) and len(bc) >= 3:
            beam_color = (int(bc[0]), int(bc[1]), int(bc[2]))
        else:
            beam_color = (0, 255, 0)

        t = (data.get("type") or "moving_head_16ch").lower()
        channels = int(data.get("channels", 8 if t.endswith("8ch") else 16))
        dimmer = float(data.get("dimmer", 1.0))
        scale = float(data.get("scale", 20.0))

        obj = cls(
            object_id,
            channels=channels,
            position=position,
            rotation=rotation,
            scale=scale,
            pan=pan,
            tilt=tilt,
            beam_on=beam_on,
            beam_color=beam_color,
            dimmer=dimmer,
        )
        obj.name = data.get("name", "")
        obj.device_config = data.get("device")

        # Reset DMX-controlled values so they come from live data, not the file.
        if obj.device_config:
            dc = obj.device_config
            mv_map = dc.get("movement", {}).get("mapping", {})
            col_map = dc.get("color", {}).get("mapping", {})
            if mv_map.get("pan_coarse", -1) >= 0:
                obj.pan = 0.0
            if mv_map.get("tilt_coarse", -1) >= 0:
                obj.tilt = 0.0
            if mv_map.get("dimmer", -1) >= 0 or col_map.get("white", -1) >= 0:
                obj.dimmer = 1.0
                obj.beam_on = True

        return obj


# Keys exposed by the "Add Fixture" dialog.
FIXTURE_KEYS = [
    "truss_default",
    "truss_2point_medium",
    "truss_cross",
    "truss_long",
    "truss_medium",
    "moving_head",
]


def create_object_from_key(fixture_key: str, object_id: str,
                           name: str = "") -> StageObject:
    """Factory: build a StageObject from one of the ``FIXTURE_KEYS``."""
    key = fixture_key.lower()
    if key.startswith("truss"):
        variant = "default" if key in ("truss", "truss_default") else key[len("truss_"):]
        obj = Truss(object_id, variant=variant)
    elif key.startswith("moving_head"):
        obj = MovingHead(object_id)
    else:
        raise ValueError(f"Unknown fixture key: {fixture_key}")
    obj.name = name
    return obj


def make_unique_name(desired_name: str, existing_names: list[str]) -> str:
    """Append ``(1)``, ``(2)``... until the name is unique."""
    if desired_name not in existing_names:
        return desired_name
    num = 1
    candidate = f"{desired_name} ({num})"
    while candidate in existing_names:
        num += 1
        candidate = f"{desired_name} ({num})"
    return candidate


class FixtureGroup:
    """Named bundle of fixtures that can be moved or rotated together.

    The group's own position is the centroid of its members at creation
    time; the editor widget applies deltas to all members when the group
    is transformed.
    """

    def __init__(self, group_id: str, name: str = "",
                 position: tuple[float, float, float] | None = None,
                 rotation: tuple[float, float, float] | None = None,
                 member_ids: list[str] | None = None):
        self.id = group_id
        self.name = name
        self.position = position if position is not None else (0.0, 0.0, 0.0)
        self.rotation = rotation if rotation is not None else (0.0, 0.0, 0.0)
        self.member_ids: list[str] = list(member_ids) if member_ids else []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "position": {"x": self.position[0], "y": self.position[1], "z": self.position[2]},
            "rotation": {"x": self.rotation[0], "y": self.rotation[1], "z": self.rotation[2]},
            "member_ids": list(self.member_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        pos = data.get("position", {})
        rot = data.get("rotation", {})
        return cls(
            data.get("id", "group"),
            data.get("name", ""),
            (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0)),
            (rot.get("x", 0.0), rot.get("y", 0.0), rot.get("z", 0.0)),
            data.get("member_ids", []),
        )


class StageConfig:
    """Aggregate root: list of objects + list of groups, persisted as YAML."""

    def __init__(self, yaml_file_path: str):
        self.file_path = yaml_file_path
        self.objects: list[StageObject] = []
        self.groups: list[FixtureGroup] = []

        if os.path.exists(self.file_path):
            try:
                yaml_loader = yaml.YAML(typ="safe")
                with open(self.file_path, "r", encoding="UTF-8") as f:
                    data = yaml_loader.load(f) or {}
            except yaml.YAMLError as e:
                logger.error("Failed to parse YAML file %s: %s", self.file_path, e)
                data = {}

            for obj_data in data.get("objects", []):
                type_name = (obj_data.get("type") or "truss").lower()
                if type_name.startswith("truss"):
                    obj = Truss.from_dict(obj_data)
                elif type_name.startswith("moving_head"):
                    obj = MovingHead.from_dict(obj_data)
                elif type_name == "platform":
                    obj = Platform.from_dict(obj_data)
                else:
                    obj = StageObject.from_dict(obj_data)
                self.objects.append(obj)

            for grp_data in data.get("groups", []):
                self.groups.append(FixtureGroup.from_dict(grp_data))
        else:
            logger.info("Stage YAML file %s not found, starting empty.", self.file_path)

        # Stage invariant: always have exactly one platform.
        if not any(o.get_type() == "platform" for o in self.objects):
            self.objects.insert(0, Platform())

    def save(self):
        self.save_to(self.file_path)

    def save_to(self, path: str):
        data = {"objects": [obj.to_dict() for obj in self.objects]}
        if self.groups:
            data["groups"] = [grp.to_dict() for grp in self.groups]
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            yaml_dumper = yaml.YAML()
            yaml_dumper.default_flow_style = False
            with open(path, "w", encoding="UTF-8") as f:
                yaml_dumper.dump(data, f)
        except Exception as e:
            logger.error("Failed to save stage config to %s: %s", path, e)

    def get_all_names(self) -> list[str]:
        names = [obj.name for obj in self.objects if obj.name]
        names += [grp.name for grp in self.groups if grp.name]
        return names

    def get_new_id(self, base_type: str = "obj") -> str:
        """Return a unique id of the form ``<base><N>``."""
        base = (base_type or "obj").lower().replace("-", "_")
        existing = {o.id for o in self.objects} | {g.id for g in self.groups}
        i = 1
        while f"{base}{i}" in existing:
            i += 1
        return f"{base}{i}"

    def add_object(self, obj: StageObject):
        if any(o.id == obj.id for o in self.objects):
            obj.id = self.get_new_id(obj.get_type())
        if obj.name:
            obj.name = make_unique_name(obj.name, self.get_all_names())
        self.objects.append(obj)

    def remove_object(self, object_id: str):
        for i, obj in enumerate(self.objects):
            if obj.id == object_id:
                removed = self.objects.pop(i)
                for grp in self.groups:
                    if object_id in grp.member_ids:
                        grp.member_ids.remove(object_id)
                return removed
        return None

    def get_object(self, object_id: str):
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        return None

    def add_group(self, group: FixtureGroup):
        if any(g.id == group.id for g in self.groups):
            group.id = self.get_new_id("group")
        if group.name:
            group.name = make_unique_name(group.name, self.get_all_names())
        self.groups.append(group)

    def remove_group(self, group_id: str) -> FixtureGroup | None:
        for i, grp in enumerate(self.groups):
            if grp.id == group_id:
                return self.groups.pop(i)
        return None

    def get_group(self, group_id: str) -> FixtureGroup | None:
        for grp in self.groups:
            if grp.id == group_id:
                return grp
        return None

    def get_group_for_fixture(self, object_id: str) -> FixtureGroup | None:
        for grp in self.groups:
            if object_id in grp.member_ids:
                return grp
        return None
