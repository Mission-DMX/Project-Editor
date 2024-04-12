# coding=utf-8
from model.virtual_filters.effects_stacks.effect import Effect


class EffectCopySymbolColorEffect:
    def __init__(self, target: Effect):
        self._target: Effect = target
        # TODO this object should return placeholders that insert the correct channel mapping once the target is in
        #  place. We need to figure out how we should do this the best way. Maybe insert all returned placeholders as
        #  str-like objects that will only evaluate to the real channel once the associated filters have been placed?
