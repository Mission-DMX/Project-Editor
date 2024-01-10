from model import Scene
from model.filter import VirtualFilter, Filter


class PanTiltConstantFilter(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, filter_type: int):
        super().__init__(scene, filter_id, filter_type)
        self._pan = 360
        self._tilt = 180

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        print("test1")
        return "error"

    def instantiate_filters(self, filter_list: list[Filter]):
        print("test2")

    @property
    def pan(self):
        return self._pan

    @pan.setter
    def pan(self, pan):
        self._pan = pan

    @property
    def tilt(self):
        return self._tilt

    @tilt.setter
    def tilt(self, tilt):
        self._tilt = tilt
