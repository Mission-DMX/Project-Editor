from logging import getLogger

from controller.ofl.fixture import UsedFixture, ColorSupport
from model.virtual_filters.effects_stacks.color_effects import ColorEffect

logger = getLogger(__file__)


class EffectsSocket:
    """
    This class contains the anchor for an effect stack on a given group or fixture.
    """

    def __init__(self, target: UsedFixture):
        self.target: UsedFixture = target  # TODO also implement support for fixture groups
        self.color_socket: list[ColorEffect] = []
        self.has_color_property: bool = target.check_for_color_property() != ColorSupport.NO_COLOR_SUPPORT

    # TODO implement serialization
