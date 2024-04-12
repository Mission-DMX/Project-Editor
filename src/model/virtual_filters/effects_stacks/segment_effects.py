# coding=utf-8
from abc import ABC

from model.virtual_filters.effects_stacks.effect import Effect, EffectType


class SegmentEffect(Effect, ABC):
    def get_output_slot_type(self):
        return EffectType.ENABLED_SEGMENTS
