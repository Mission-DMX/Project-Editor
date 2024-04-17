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
        self.deserialize()

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

            zero_constant_name = "{}__blank_color_slot_constant__{}_{}".format(
                self.filter_id, socket_target.parent_universe, socket_target.__hash__()
            )
            zero_constant_8bit_required: bool = False
            zero_constant_float_required: bool = False
            if socket.has_color_property:
                color_effect = socket.get_socket_by_type(EffectType.COLOR)
                if color_effect is not None:
                    filter_prefix = "{}__coloreffect_{}_{}".format(
                        self.filter_id,
                        socket_target.parent_universe,
                        socket_target.channels[0].address
                    )
                    output_dict = color_effect.emplace_filter(filter_list, filter_prefix)
                    output_dict = emplace_adapter(color_effect.get_output_slot_type(), EffectType.COLOR,
                                                  output_dict, filter_list)

                    if not isinstance(output_dict["color"], list):
                        output_dict["color"] = [output_dict["color"]]
                    if socket.has_segmentation_support:
                        segmentation_effect = socket.get_socket_by_type(EffectType.ENABLED_SEGMENTS)
                        if segmentation_effect:
                            filter_prefix = "{}__segmentation_{}_{}".format(
                                self.filter_id,
                                socket_target.parent_universe,
                                socket_target.channels[0].address
                            )
                            segmentation_outputs = segmentation_effect.emplace_filter(filter_list, filter_prefix)
                            segmentation_outputs = emplace_adapter(segmentation_effect.get_output_slot_type(),
                                                                   EffectType.ENABLED_SEGMENTS,
                                                                   segmentation_outputs,
                                                                   filter_list)
                            i = 0
                            for segment_number, segment_out_port in segmentation_outputs.items():
                                color_index = i % len(output_dict["color"])
                                seg_split_filter_name = "{}__universeoutput__segmentsplitter_{}_{}__{}".format(
                                    self.filter_id, socket_target.parent_universe,
                                    socket_target.channels[0].address, segment_number
                                )
                                split_filter = Filter(self.scene, seg_split_filter_name, 53, self.pos)  # TODO rename
                                split_filter.channel_links["input"] = output_dict["color"][color_index]
                                filter_list.append(split_filter)
                                multiply_filter_i = Filter(self.scene, seg_split_filter_name + "_multiply",
                                                           FilterTypeEnumeration.FILTER_ARITHMETICS_MAC, self.pos)
                                multiply_filter_i.channel_links["factor_1"] = segment_out_port
                                multiply_filter_i.channel_links["factor_2"] = seg_split_filter_name + ":i"
                                multiply_filter_i.channel_links["summand"] = zero_constant_name + "_float:value"
                                zero_constant_float_required = True
                                filter_list.append(multiply_filter_i)
                                combination_filter = Filter(self.scene, seg_split_filter_name + "_combine",
                                                            18, self.pos) # TODO rename
                                combination_filter.channel_links["h"] = seg_split_filter_name + ":h"
                                combination_filter.channel_links["s"] = seg_split_filter_name + ":s"
                                combination_filter.channel_links["i"] = seg_split_filter_name + "_multiply:value"
                                filter_list.append(combination_filter)
                                output_dict["color"][color_index] = seg_split_filter_name + "_combine:value"
                                i += 1

                    color_adapter_name_base = "{}__color_adapter_property"
                    color_support_of_target = socket_target.color_support()

                    adapter_filters = []
                    for i in range(len(output_dict["color"])):
                        if color_support_of_target == ColorSupport.HAS_RGB_SUPPORT:
                            adapter_filter = Filter(self.scene, color_adapter_name_base, 15, self.pos) # TODO rename type
                        elif color_support_of_target == ColorSupport.HAS_RGB_SUPPORT | ColorSupport.HAS_WHITE_SEGMENT:
                            adapter_filter = Filter(self.scene, color_adapter_name_base, 16, self.pos)  # TODO rename type
                        elif color_support_of_target == ColorSupport.HAS_RGB_SUPPORT | ColorSupport.HAS_WHITE_SEGMENT | ColorSupport.HAS_AMBER_SEGMENT:
                            adapter_filter = Filter(self.scene, color_adapter_name_base, 17, self.pos)  # TODO rename type
                        # TODO advance adapter selection to further combinations

                        filter_list.append(adapter_filter)
                        adapter_filter.channel_links["value"] = output_dict["color"][i]
                        adapter_filters.append(adapter_filter)

                    # TODO handle uv
                    for segment_channel_name, segment_list in [
                            ("r", socket_target.red_segments), ("g", socket_target.green_segments),
                            ("b", socket_target.blue_segments), ("w", socket_target.white_segments),
                            ("a", socket_target.amber_segments)]:
                        i = 0
                        for segment in segment_list:
                            universe_filter.filter_configurations[str(segment.address)] = str(segment.address)
                            universe_filter.channel_links[str(segment.address)] = "{}:{}".format(
                                adapter_filters[i % len(adapter_filters)].filter_id, segment_channel_name)
                            i += 1
                else:
                    for segment_list in [socket_target.red_segments, socket_target.green_segments,
                                         socket_target.blue_segments, socket_target.white_segments,
                                         socket_target.amber_segments, socket_target.uv_segments]:
                        for rs in segment_list:
                            universe_filter.filter_configurations[rs.fixture_channel] = str(rs.address)
                            universe_filter.channel_links[rs.fixture_channel] = zero_constant_name + "_8bit:value"
                            zero_constant_8bit_required = True
            # TODO implement other slot types
            #  (except for EffectType.ENABLED_SEGMENTS which will be handled together with the color)
            if zero_constant_8bit_required:
                constant_filter = Filter(self.scene, zero_constant_name + "_8bit",
                                         FilterTypeEnumeration.FILTER_CONSTANT_8BIT, self.pos)
                constant_filter.initial_parameters["value"] = "0"
                filter_list.append(constant_filter)
            if zero_constant_float_required:
                constant_filter = Filter(self.scene, zero_constant_name + "_float",
                                         FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, self.pos)
                constant_filter.initial_parameters["value"] = "0.0"
                filter_list.append(constant_filter)

    def filter_configurations(self) -> dict[str, str]:
        d = {}
        for s in self.sockets:
            name = "{}/{}/{}".format('g' if s.is_group else 'f', s.target.parent_universe,
                                     s.target.channels[0].address)
            d[name] = s.serialize()
        return d

    def deserialize(self):
        pass  # TODO implement deserialization of filter

    # TODO implement optional output ports of effect stack vfilter

