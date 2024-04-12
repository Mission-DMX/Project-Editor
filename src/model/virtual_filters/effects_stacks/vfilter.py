from model import Filter, Scene
from model.filter import VirtualFilter, FilterTypeEnumeration
from model.virtual_filters.effects_stacks.effect_socket import EffectsSocket


class EffectsStack(VirtualFilter):

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_EFFECTSSTACK, pos=pos)
        self.sockets: list[EffectsSocket] = []

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        pass

    def instantiate_filters(self, filter_list: list[Filter]):
        pass

    # TODO implement serialization
