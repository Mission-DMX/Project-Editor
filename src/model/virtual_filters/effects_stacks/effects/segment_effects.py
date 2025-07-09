
"""This file implements effects that manipulate the enabled segments."""

from abc import ABC

from model.virtual_filters.effects_stacks.effect import Effect, EffectType


class SegmentEffect(Effect, ABC):
    """Base class for segment effects"""
    def get_output_slot_type(self)->EffectType:
        return EffectType.ENABLED_SEGMENTS
