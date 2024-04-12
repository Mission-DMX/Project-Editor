from controller.ofl.fixture import ColorSupport
from model import Filter, Scene
from model.filter import VirtualFilter, FilterTypeEnumeration
from model.virtual_filters.effects_stacks.adapters import emplace_adapter
from model.virtual_filters.effects_stacks.effect import EffectType
from model.virtual_filters.effects_stacks.effect_socket import EffectsSocket


class EffectsStack(VirtualFilter):

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_EFFECTSSTACK, pos=pos)
        self.sockets: list[EffectsSocket] = []

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        # We only need to resolve ports for explicitly configured outputs
        pass

    def instantiate_filters(self, filter_list: list[Filter]):
        for socket in self.sockets:
            socket_target = socket.target
            universe_filter: Filter = Filter(self.scene, "{}__universeoutput__{}_{}".format(
                self.filter_id, socket_target.parent_universe, socket_target.channels[0].address),
                                             FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT)
            universe_filter.filter_configurations["universe"] = str(socket_target.parent_universe)
            filter_list.append(universe_filter)
            if socket.has_color_property:
                color_effect = socket.get_socket_by_type(EffectType.COLOR)
                if color_effect is not None:
                    output_dict = color_effect.emplace_filter(filter_list)
                    output_dict = emplace_adapter(color_effect.get_output_slot_type(), EffectType.COLOR,
                                                  output_dict, filter_list)
                    # TODO multiply the intensity channels with the segment selection information for every segment pair
                    #  if there is a segment specialization input to this socket
                    color_adapter_name = "{}__color_adapter_property"
                    color_support_of_target = socket_target.color_support()
                    if color_support_of_target == ColorSupport.HAS_RGB_SUPPORT:
                        adapter_filter = Filter(self.scene, color_adapter_name, 15, self.pos)
                        # TODO replace 15 with Adapter name once cue preview branch has been merged.
                    elif color_support_of_target == ColorSupport.HAS_RGB_SUPPORT | ColorSupport.HAS_WHITE_SEGMENT:
                        adapter_filter = Filter(self.scene, color_adapter_name, 16, self.pos)  # TODO rename type
                    elif color_support_of_target == ColorSupport.HAS_RGB_SUPPORT | ColorSupport.HAS_WHITE_SEGMENT | ColorSupport.HAS_AMBER_SEGMENT:
                        adapter_filter = Filter(self.scene, color_adapter_name, 17, self.pos)  # TODO rename type
                    # TODO advance adapter selection to further combinations

                    filter_list.append(adapter_filter)
                    adapter_filter.channel_links["value"] = output_dict["color"]
                    # TODO handle uv
                    for segment_channel_name, segment_list in [
                            ("r", socket_target.red_segments), ("g", socket_target.green_segments),
                            ("b", socket_target.blue_segments), ("w", socket_target.white_segments),
                            ("a", socket_target.amber_segments)]:
                        for segment in segment_list:
                            universe_filter.filter_configurations[str(segment.address)] = str(segment.address)
                            universe_filter.channel_links[str(segment.address)] = "{}:{}".format(
                                adapter_filter.filter_id, segment_channel_name)
                else:
                    constant_filter_id = "{}__blank_color_slot_constant__{}_{}".format(
                        self.filter_id, socket_target.parent_universe, socket_target.__hash__()
                    )
                    constant_filter = Filter(self.scene, constant_filter_id,
                                             FilterTypeEnumeration.FILTER_CONSTANT_8BIT, self.pos)
                    constant_filter.initial_parameters["value"] = "0"
                    filter_list.append(constant_filter)
                    for segment_list in [socket_target.red_segments, socket_target.green_segments,
                                         socket_target.blue_segments, socket_target.white_segments,
                                         socket_target.amber_segments, socket_target.uv_segments]:
                        for rs in segment_list:
                            universe_filter.filter_configurations[rs.fixture_channel] = str(rs.address)
                            universe_filter.channel_links[rs.fixture_channel] = constant_filter_id + ":value"
            # TODO implement other slot types
            #  (except for EffectType.ENABLED_SEGMENTS which will be handled together with the color)

    # TODO implement serialization
    # TODO implement outputs

