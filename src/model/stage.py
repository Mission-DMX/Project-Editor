import os
import logging
from ruamel import yaml

from utility import resource_path

logger = logging.getLogger(__file__)

DEFAULT_MODEL_PATHS = {
    # TODO there are multiple variants of trusses (2-point, 3-point, 4-point, different lengths, different sizes)
    "truss": resource_path(os.path.join("resources", "3dmodels", "truss.obj")),
    "truss-cross": resource_path(os.path.join("resources", "3dmodels", "truss_cross.obj")),
    # TODO these are part of the general moving head model, therefore this dict should address this
    "moving_head_base": resource_path(os.path.join("resources", "3dmodels", "mh_base.obj")),
    "moving_head_arm": resource_path(os.path.join("resources", "3dmodels", "mh_arm.obj")),
    "moving_head_light": resource_path(os.path.join("resources", "3dmodels", "mh_light.obj")),
}

class StageObject:

    def __init__(self, object_id: str, position=None, rotation=None):
        self.id = object_id
        self.position = position if position is not None else (0.0, 0.0, 0.0)
        self.rotation = rotation if rotation is not None else (0.0, 0.0, 0.0)
        self.model_path = DEFAULT_MODEL_PATHS[self.get_type().lower()]

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.get_type(),
            'position': {'x': self.position[0], 'y': self.position[1], 'z': self.position[2]},
            'rotation': {'x': self.rotation[0], 'y': self.rotation[1], 'z': self.rotation[2]}
        }

    @classmethod
    def from_dict(cls, data: dict):
        object_id = data.get('id')
        pos = data.get('position', {})
        rot = data.get('rotation', {})
        position = (pos.get('x', 0.0), pos.get('y', 0.0), pos.get('z', 0.0))
        rotation = (rot.get('x', 0.0), rot.get('y', 0.0), rot.get('z', 0.0))
        return cls(object_id, position, rotation)

    def get_type(self) -> str:
        return "default"


class Truss(StageObject):

    def __init__(self, object_id: str, position=None, rotation=None):
        super().__init__(object_id, position, rotation)

    def get_type(self):
        return "truss"


class MovingHead(StageObject):

    def __init__(self, object_id: str, position=None, rotation=None, pan=0.0, tilt=0.0):
        super().__init__(object_id, position, rotation)
        self.pan = pan
        self.tilt = tilt

    def get_type(self):
        return "moving_head"

    def to_dict(self):
        data = super().to_dict()
        data.update({'pan': self.pan, 'tilt': self.tilt})
        return data

    @classmethod
    def from_dict(cls, data: dict):
        object_id = data.get('id')
        pos = data.get('position', {})
        rot = data.get('rotation', {})
        pan = data.get('pan', 0.0);
        tilt = data.get('tilt', 0.0)
        position = (pos.get('x', 0.0), pos.get('y', 0.0), pos.get('z', 0.0))
        rotation = (rot.get('x', 0.0), rot.get('y', 0.0), rot.get('z', 0.0))
        return cls(object_id, position, rotation, pan, tilt)


class StageConfig:

    def __init__(self, yaml_file_path: str):
        self.file_path = yaml_file_path
        self.objects: list[StageObject] = []
        if os.path.exists(self.file_path):
            try:
                yaml_loader = yaml.YAML(typ='safe')
                with open(self.file_path, 'r', encoding='UTF-8') as f:
                    data = yaml_loader.load(f) or {}
            except yaml.YAMLError as e:
                logger.error("Failed to parse YAML file %s: %s", self.file_path, e)
                data = {}
            obj_list = data.get('objects', [])
            for obj_data in obj_list:
                type_name = obj_data.get('type', 'truss')
                if type_name == 'truss':
                    obj = Truss.from_dict(obj_data)
                elif type_name == 'moving_head':
                    obj = MovingHead.from_dict(obj_data)
                else:
                    obj = StageObject.from_dict(obj_data)
                self.objects.append(obj)
        else:
            logger.info("Stage YAML file %s not found, starting with empty config.", self.file_path)
            self.objects = []

    def save(self):
        data = {'objects': [obj.to_dict() for obj in self.objects]}
        try:
            yaml_dumper = yaml.YAML()
            yaml_dumper.default_flow_style = False
            with open(self.file_path, 'w', encoding='UTF-8') as f:
                yaml_dumper.dump(data, f)
        except Exception as e:
            logger.error("Failed to save stage config to %s: %s", self.file_path, e)

    def get_new_id(self, base_type: str = "obj"):
        base = base_type.lower()
        i = 1
        existing_ids = {obj.id for obj in self.objects}
        new_id = f"{base}{i}"
        while new_id in existing_ids:
            i += 1
            new_id = f"{base}{i}"
        return new_id

    def add_object(self, obj: StageObject):
        # Assign unique ID to object
        if any(o.id == obj.id for o in self.objects):
            obj.id = self.get_new_id(obj.get_type())
        self.objects.append(obj)

    def remove_object(self, object_id: str):
        for i, obj in enumerate(self.objects):
            if obj.id == object_id:
                removed = self.objects.pop(i)
                return removed
        return None

    def get_object(self, object_id: str):
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        return None