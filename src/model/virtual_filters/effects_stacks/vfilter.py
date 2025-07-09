"""This file provides the v-filter implementation of the effects stack system"""

from logging import getLogger

from model import Filter, Scene
from model.filter import FilterTypeEnumeration, VirtualFilter
from model.ofl.fixture import ColorSupport
from model.patching.fixture_channel import FixtureChannelType
from model.virtual_filters.effects_stacks.adapters import emplace_with_adapter
from model.virtual_filters.effects_stacks.effect import EffectType
from model.virtual_filters.effects_stacks.effect_socket import EffectsSocket

logger = getLogger(__file__)


class EffectsStack(VirtualFilter):
    """The v-filter providing the effects stack. This filter provides a system enabling one to assign stackable effects
    to fixtures, groups of fixtures or configurable output ports."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_EFFECTSSTACK, pos=pos)
        self.sockets: list[EffectsSocket] = []
        self.deserialize()

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        # We only need to resolve ports for explicitly configured outputs
        pass

    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        for socket in self.sockets:
            socket_target = socket.target
            universe_filter: Filter = Filter(self.scene,
                                             f"{self.filter_id}__universeoutput__{socket_target.parent_universe}"
                                             f"_{socket_target.start_index}",
                                             FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT)
            universe_filter.filter_configurations["universe"] = str(socket_target.parent_universe)
            filter_list.append(universe_filter)

            zero_constant_name = (f"{self.filter_id}__blank_color_slot_constant__"
                                  f"{socket_target.parent_universe}_{socket_target.__hash__()}")
            zero_constant_8bit_required: bool = False
            zero_constant_float_required: bool = False
            if socket.has_color_property:
                color_effect = socket.get_socket_by_type(EffectType.COLOR)
                if color_effect is not None:
                    filter_prefix = (f"{self.filter_id}__coloreffect_{socket_target.parent_universe}_"
                                     f"{socket_target.start_index}")
                    output_dict = emplace_with_adapter(color_effect, EffectType.COLOR, filter_list, filter_prefix)

                    if not isinstance(output_dict["color"], list):
                        output_dict["color"] = [output_dict["color"]]
                    if len(output_dict["color"]) == 0:
                        logger.error("Color Effect '%s' did not produce any output.", color_effect)
                    if socket.has_segmentation_support:
                        segmentation_effect = socket.get_socket_by_type(EffectType.ENABLED_SEGMENTS)
                        if segmentation_effect:
                            filter_prefix = (f"{self.filter_id}__segmentation_{socket_target.parent_universe}_"
                                             f"{socket_target.start_index}")
                            segmentation_outputs = emplace_with_adapter(segmentation_effect,
                                                                        EffectType.ENABLED_SEGMENTS,
                                                                        filter_list, filter_prefix)

                            for i, segment_number, segment_out_port in enumerate(segmentation_outputs.items()):
                                color_index = i % len(output_dict["color"])
                                seg_split_filter_name = (f"{self.filter_id}__universeoutput__segmentsplitter_"
                                                         f"{socket_target.parent_universe}_"
                                                         f"{socket_target.start_index}__{segment_number}")
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
                                                            18, self.pos)  # TODO rename
                                combination_filter.channel_links["h"] = seg_split_filter_name + ":h"
                                combination_filter.channel_links["s"] = seg_split_filter_name + ":s"
                                combination_filter.channel_links["i"] = seg_split_filter_name + "_multiply:value"
                                filter_list.append(combination_filter)
                                output_dict["color"][color_index] = seg_split_filter_name + "_combine:value"

                    color_adapter_name_base = f"{filter_prefix}__color_adapter_property"
                    color_support_of_target = socket_target.color_support

                    adapter_filters = []
                    for i in range(len(output_dict["color"])):
                        if color_support_of_target == ColorSupport.HAS_RGB_SUPPORT:
                            adapter_filter = Filter(self.scene, color_adapter_name_base, 15,
                                                    self.pos)  # TODO rename type
                        elif color_support_of_target == ColorSupport.HAS_RGB_SUPPORT | ColorSupport.HAS_WHITE_SEGMENT:
                            adapter_filter = Filter(self.scene, color_adapter_name_base, 16,
                                                    self.pos)  # TODO rename type
                        elif (color_support_of_target == ColorSupport.HAS_RGB_SUPPORT |
                              ColorSupport.HAS_WHITE_SEGMENT | ColorSupport.HAS_AMBER_SEGMENT):
                            adapter_filter = Filter(self.scene, color_adapter_name_base, 17,
                                                    self.pos)  # TODO rename type
                        # TODO advance adapter selection to further combinations

                        filter_list.append(adapter_filter)
                        adapter_filter.channel_links["value"] = output_dict["color"][i]
                        adapter_filters.append(adapter_filter)

                    # TODO handle uv
                    # TODO handle main brightness control
                    for segment_channel_name, segment_list in [
                        ("r", socket_target.get_segment_in_universe_by_type(FixtureChannelType.RED)),
                        ("g", socket_target.get_segment_in_universe_by_type(FixtureChannelType.GREEN)),
                        ("b", socket_target.get_segment_in_universe_by_type(FixtureChannelType.BLUE)),
                        ("w", socket_target.get_segment_in_universe_by_type(FixtureChannelType.WHITE)),
                        ("a", socket_target.get_segment_in_universe_by_type(FixtureChannelType.AMBER))]:
                        i = 0
                        for segment in segment_list:
                            universe_filter.filter_configurations[str(segment)] = str(segment)
                            universe_filter.channel_links[str(segment)] = \
                                f"{adapter_filters[i % len(adapter_filters)].filter_id}:{segment_channel_name}"
                            i += 1
                else:
                    for segment_list in [socket_target.get_segment_in_universe_by_type(FixtureChannelType.RED),
                                         socket_target.get_segment_in_universe_by_type(FixtureChannelType.GREEN),
                                         socket_target.get_segment_in_universe_by_type(FixtureChannelType.BLUE),
                                         socket_target.get_segment_in_universe_by_type(FixtureChannelType.WHITE),
                                         socket_target.get_segment_in_universe_by_type(FixtureChannelType.AMBER),
                                         socket_target.get_segment_in_universe_by_type(FixtureChannelType.UV)]:
                        for segment in segment_list:
                            fixture_chanel_name: str = socket_target.get_fixture_channel(
                                segment - socket_target.start_index).name
                            universe_filter.filter_configurations[fixture_chanel_name] = str(segment)
                            universe_filter.channel_links[fixture_chanel_name] = zero_constant_name + "_8bit:value"
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

    def serialize(self) -> None:
        d = self.filter_configurations
        d.clear()
        for s in self.sockets:
            name = f"{'g' if s.is_group else 'f'}{s.target.universe_id}/{s.target.start_index}"
            # TODO Encode start addresses in case of group or use uuid of fixture
            d[name] = s.serialize()

    def deserialize(self) -> None:
        self.sockets.clear()
        for k, v in self._filter_configurations.items():
            is_group = k.startswith("g")
            if is_group:
                raise NotImplementedError("Deserialization of groups is not yet implemented.")

            universe, channel = k[1:].split("/")
            universe = int(universe)
            channel = int(channel)
            for fixture in self.scene.board_configuration.fixtures:
                if fixture.universe_id == universe and fixture.start_index == channel:
                    uf = fixture
            if uf is None:
                logger.warning(
                    "There is no fixture associated with the address %s/%s", universe, channel + 1,
                )
                continue
            s = EffectsSocket(uf)
            s.deserialize(v, self)
            self.sockets.append(s)

    # TODO implement optional output ports of effect stack vfilter
