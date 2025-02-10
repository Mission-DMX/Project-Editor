# coding=utf-8

"""This file contains an effect factory for obtaining effects in the context of restoring a show file state."""

from typing import TYPE_CHECKING

from model.virtual_filters.effects_stacks.effect import Effect
from model.virtual_filters.effects_stacks.effects.color_effects import ColorWheelEffect
from model.virtual_filters.effects_stacks.effects.fader_input_effects import ColorInputEffect
from model.virtual_filters.effects_stacks.effects.generic_effects import FunctionEffect

if TYPE_CHECKING:
    from model.virtual_filters.effects_stacks.vfilter import EffectsStack


def effect_from_deserialization(effect_description: dict[str, str], f: "EffectsStack") -> Effect:
    """Get an effect from a context dictionary representation.

    Note: this method may raise a ValueError exception in case that the requested effect type is unknown or not yet
    implemented.

    :param effect_description: The context dictionary of the effect that should be restored.
    :param f: The parent effects v-filter of the effect.
    :returns: the full restored effect.
    """

    effect_type = effect_description.get("type")
    match effect_type:
        case "color.InputFader":
            e = ColorInputEffect()
        case "generic.function":
            e = FunctionEffect()
        case ColorWheelEffect.EFFECT_ID:
            e = ColorWheelEffect()
        # TODO implement __copysymbol__
        case _:
            raise ValueError("The effect type '{}' cannot be instantiated. Have you forgotten to implement it?".format(
                effect_type
            ))
    e.set_parent_filter(f)
    e.deserialize(effect_description)
    return e
