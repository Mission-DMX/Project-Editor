# coding=utf-8
"""This file contains adapters between different effect output types that can be instantiated."""

from model import Filter
from model.filter import FilterTypeEnumeration
from model.virtual_filters.effects_stacks.effect import Effect, EffectType


def emplace_with_adapter(input_effect: Effect, target_type: EffectType,
                         filter_list: list[Filter], name_prefix: str) -> dict[str, str | list[str]]:
    """This method instantiates the given effect and instantiates required adapter filters if required.
    If the provided type and the desired type are already compatible, this method returns the input_dict as-is.

    Note: this method requires the filter_list to be already non-empty as certain information, such as the target scene
    are deduced from the first existing filter in the list.

    :param input_effect: The effect of which the filters are supposed to be instantiated and which is adapted from.
    :param target_type: The type the calling placement agent required.
    :param filter_list: The list of filters that can be used for placement.
    :param name_prefix: The name prefix to use for instantiation.
    :returns: A new dictionary containing the translated output ports or input_dict if it was already compatible.
    """
    given_type = input_effect.get_output_slot_type()
    input_dict = input_effect.emplace_filter(filter_list, name_prefix)
    if given_type == target_type:
        return input_dict
    match target_type:
        case EffectType.LIGHT_INTENSITY:
            if given_type == EffectType.GENERIC_NUMBER:
                conv_f = Filter(filter_list[-1].scene, name_prefix + "+adapter_number_to_light",
                                FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE)
                conv_f.channel_links['value_in'] = input_dict['x']
                filter_list.append(conv_f)
                return {'intensity': name_prefix + "+adapter_number_to_light:value"}
        case EffectType.GOBO_SELECTION:
            if given_type == EffectType.GENERIC_NUMBER:
                conv_f = Filter(filter_list[-1].scene, name_prefix + "+adapter_number_to_gobo",
                                FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE)
                conv_f.channel_links['value_in'] = input_dict['x']
                filter_list.append(conv_f)
                return {'gobo': name_prefix + "+adapter_number_to_gobo:value"}
        case EffectType.ZOOM_FOCUS:
            if given_type == EffectType.GENERIC_NUMBER:
                conv_f = Filter(filter_list[-1].scene, name_prefix + "+adapter_number_to_zf",
                                FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE)
                conv_f.channel_links['value_in'] = input_dict['x']
                filter_list.append(conv_f)
                return {'zoom': name_prefix + "+adapter_number_to_zf:value",
                        'focus': name_prefix + "+adapter_number_to_zf:value"}
        case EffectType.SHUTTER_STROBE:
            if given_type == EffectType.GENERIC_NUMBER:
                conv_f = Filter(filter_list[-1].scene, name_prefix + "+adapter_number_to_strobe",
                                FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE,
                                initial_parameters={'upper_bound_out': '40'})
                conv_f.channel_links['value_in'] = input_dict['x']
                filter_list.append(conv_f)
                return {'shutter': name_prefix + "+adapter_number_to_strobe:value"}
    raise NotImplementedError("Please implement the adapter instantiation.")
