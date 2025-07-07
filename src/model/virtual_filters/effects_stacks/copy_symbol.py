
"""
This file contains the copy symbol placeholders for the effects stack system.
A copy symbol is an effect stub that behaves like a regular effect while filters are instantiated but will
redirect the channels to a different (target) effect. This way the output of an effect can be liked to the input of a
different one.

Note: This file is WIP!
"""

from model.virtual_filters.effects_stacks.effect import Effect


class EffectCopySymbolColorEffect:
    """A copy symbol for color effects."""
    def __init__(self, target: Effect):
        self._target: Effect = target
        # TODO this object should return placeholders that insert the correct channel mapping once the target is in
        #  place. We need to figure out how we should do this the best way. Maybe insert all returned placeholders as
        #  str-like objects that will only evaluate to the real channel once the associated filters have been placed?
