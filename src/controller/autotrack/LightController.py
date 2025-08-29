"""Abstract base class for controlling lights."""

import asyncio
from abc import ABC, abstractmethod


class LightController(ABC):
    """The `LightController` class is an abstract base class for controlling lights.

    Methods:
        - `turn_on()`: Abstract method to turn on the light(s).
        - `turn_off()`: Abstract method to turn off the light(s).
        - `set_brightness(brightness)`: Abstract method to set the brightness of the light(s).
        - `set_position(position)`: Abstract method to set the position or orientation of the light(s).
        - `set_color(color)`: Abstract method to set the color of the light(s).

    """

    def __init__(self):
        """LightController."""
        self.corners = [[0, 0], [0, 0], [0, 0], [0, 0]]
        pass

    @abstractmethod
    def turn_on(self):
        """Abstract method to turn on the light(s)."""
        pass

    @abstractmethod
    def turn_off(self):
        """Abstract method to turn off the light(s)."""
        pass

    @abstractmethod
    def set_brightness(self, brightness: float):
        """Abstract method to set the brightness of the light(s).

        Args:
            brightness (float): The brightness level, typically in the range [0.0, 1.0].

        """
        pass

    @abstractmethod
    def set_position(self, position: tuple[int, int]):
        """Abstract method to set the position or orientation of the light(s).

        Args:
            position (tuple): The position or orientation parameters, specific to the type of light controller.

        """
        pass

    @abstractmethod
    def set_color(self, color: str):
        """Abstract method to set the color of the light(s).

        Args:
            color (str): The color to set for the light(s), specified as a string or other format.

        """
        pass

    async def frame(
        self, time: int, corners: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]
    ):
        """Illuminates the passed corners if the frame one-by-one.

        Args:
            time: The time for this operation in ms
            corners: The coordinates of the corners to illuminate

        """
        timing = time / 5
        self.set_position(corners[0])
        await asyncio.sleep(0.5 + timing)
        self.set_position(corners[1])
        await asyncio.sleep(0.5 + timing)
        self.set_position(corners[3])
        await asyncio.sleep(0.5 + timing)
        self.set_position(corners[2])
        await asyncio.sleep(0.5 + timing)
        self.set_position(corners[0])
        await asyncio.sleep(timing)
