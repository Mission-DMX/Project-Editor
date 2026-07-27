"""Stage configuration: data model, YAML persistence and fixture classes.

Objects on the stage are subclasses of ``StageObject`` (Truss, MovingHead,
Platform). ``StageConfig`` is the aggregate root that loads and saves
the full stage to a YAML file under ``~/.local/share/missionDMX/stage/``.
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from logging import getLogger

from ruamel import yaml

from model.visualizer.stage.fixture_group import FixtureGroup
from model.visualizer.stage.paths import DEFAULT_STAGE_PATH, STAGE_DIR
from model.visualizer.stage.so_moving_head import MovingHead
from model.visualizer.stage.so_platform import Platform
from model.visualizer.stage.so_truss import Truss
from model.visualizer.stage.stage_object import StageObject
from utility import resource_path

logger = getLogger(__name__)


def get_default_stage_path() -> str:
    """Return the persistent stage file path, creating it on first run."""
    os.makedirs(STAGE_DIR, exist_ok=True)
    if not os.path.exists(DEFAULT_STAGE_PATH):
        bundled = resource_path(os.path.join("resources", "data", "default_stage.yaml"))
        if os.path.exists(bundled):
            shutil.copy2(bundled, DEFAULT_STAGE_PATH)
            logger.info("Copied bundled stage.yaml to %s", DEFAULT_STAGE_PATH)
    return DEFAULT_STAGE_PATH


def backup_stage_file(stage_path: str) -> str:
    """Write a timestamped copy next to the stage file; return its path."""
    if not os.path.exists(stage_path):
        return ""
    directory = os.path.dirname(stage_path)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # NOQA: DTZ005 We'd like to get local time zone.
    backup_path = os.path.join(directory, f"stage_backup_{timestamp}.yaml")
    shutil.copy2(stage_path, backup_path)
    logger.info("Stage backup created: %s", backup_path)
    return backup_path


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


class StageConfig:
    """Aggregate root: list of objects + list of groups, persisted as YAML."""

    def __init__(self, yaml_file_path: str) -> None:
        """Initialize stage configuration."""
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

    def save(self) -> None:
        """Save the configuration to the last known file path."""
        self.save_to(self.file_path)

    def save_to(self, path: str) -> None:
        """Save the configuration to the given path.

        Args:
            path: Path to save to.

        """
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
        """Get a list of all object and group names present in stage configuration."""
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

    def add_object(self, obj: StageObject) -> None:
        """Add a new StageObject to the stage configuration."""
        if any(o.id == obj.id for o in self.objects):
            obj.id = self.get_new_id(obj.get_type())
        if obj.name:
            obj.name = make_unique_name(obj.name, self.get_all_names())
        self.objects.append(obj)

    def remove_object(self, object_id: str) -> None:
        """Remove a StageObject from the stage configuration specified by its ID."""
        for i, obj in enumerate(self.objects):
            if obj.id == object_id:
                removed = self.objects.pop(i)
                for grp in self.groups:
                    if object_id in grp.member_ids:
                        grp.member_ids.remove(object_id)
                return removed
        return None

    def get_object(self, object_id: str) -> None:
        """Get a StageObject by its ID."""
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        return None

    def add_group(self, group: FixtureGroup) -> None:
        """Add a group to the stage configuration."""
        if any(g.id == group.id for g in self.groups):
            group.id = self.get_new_id("group")
        if group.name:
            group.name = make_unique_name(group.name, self.get_all_names())
        self.groups.append(group)

    def remove_group(self, group_id: str) -> FixtureGroup | None:
        """Remove a FixtureGroup from the stage configuration, specified by its ID."""
        for i, grp in enumerate(self.groups):
            if grp.id == group_id:
                return self.groups.pop(i)
        return None

    def get_group(self, group_id: str) -> FixtureGroup | None:
        """Get a FixtureGroup by its ID."""
        for grp in self.groups:
            if grp.id == group_id:
                return grp
        return None

    def get_group_for_fixture(self, object_id: str) -> FixtureGroup | None:
        """Get the FixtureGroup a StageObject is associated with based on the ID of the StageObject.

        Returns:
            FixtureGroup | None based on a group being found.

        """
        for grp in self.groups:
            if object_id in grp.member_ids:
                return grp
        return None
