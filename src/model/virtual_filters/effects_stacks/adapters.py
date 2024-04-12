# coding=utf-8
"""This file contains adapters between different effect output types that can be instantiated."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model import Filter
    from model.virtual_filters.effects_stacks.effect import EffectType


def emplace_adapter(given_type: "EffectType", target_type: "EffectType",
                    input_dict: dict[str, str | list[str]], filter_list: list["Filter"]) -> dict[str, str | list[str]]:
    """This method instantiates required adapter filters. If the provided type and the desired type are already
    compatible, this method returns the input_dict as-is.

    Note: this method requires the filter_list to be already non-empty as certain information, such as the target scene
    are deduced from the first existing filter in the list.

    :param given_type: The type that was provided by the existing filters.
    :param target_type: The type the calling placement agent required.
    :param input_dict: The dictionary of output types the existing effect provided.
    :param filter_list: The list of filters that can be used for placement.
    :returns: A new dictionary containing the translated output ports or input_dict if it was already compatible.
    """
    pass  # TODO implement
    raise NotImplementedError("Please implement the adapter instantiation.")
