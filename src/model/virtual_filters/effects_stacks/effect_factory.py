from model.virtual_filters.effects_stacks.effect import Effect
from model.virtual_filters.effects_stacks.effects.color_effects import ColorWheelEffect
from model.virtual_filters.effects_stacks.effects.fader_input_effects import ColorInputEffect
from model.virtual_filters.effects_stacks.effects.generic_effects import FunctionEffect


def effect_from_deserialization(effect_description: dict[str, str]) -> Effect:

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
    e.deserialize(effect_description)
    return e
