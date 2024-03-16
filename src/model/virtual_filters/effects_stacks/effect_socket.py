from logging import getLogger

from model.virtual_filters.effects_stacks.color_effects import ColorEffect

logger = getLogger(__file__)


class EffectsSocket:
    """
    This class contains the anchor for an effect stack on a given group or fixture.
    """

    def __init__(self):
        self.color_socket: list[ColorEffect] = []
