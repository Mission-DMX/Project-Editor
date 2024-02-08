from abc import ABC, abstractmethod


class LightController(ABC):
    """
    The `LightController` class is an abstract base class for controlling lights.

    Methods:
        - `turn_on()`: Abstract method to turn on the light(s).
        - `turn_off()`: Abstract method to turn off the light(s).
        - `set_brightness(brightness)`: Abstract method to set the brightness of the light(s).
        - `set_position(position)`: Abstract method to set the position or orientation of the light(s).
        - `set_color(color)`: Abstract method to set the color of the light(s).

    """

    def __init__(self):
        self.corners = [[0, 0], [0, 0], [0, 0], [0, 0]]
        pass

    @abstractmethod
    def turn_on(self):
        """
        Abstract method to turn on the light(s).
        """
        pass

    @abstractmethod
    def turn_off(self):
        """
        Abstract method to turn off the light(s).
        """
        pass

    @abstractmethod
    def set_brightness(self, brightness):
        """
        Abstract method to set the brightness of the light(s).

        Args:
            brightness (float): The brightness level, typically in the range [0.0, 1.0].
        """
        pass

    @abstractmethod
    def set_position(self, position):
        """
        Abstract method to set the position or orientation of the light(s).

        Args:
            position (tuple): The position or orientation parameters, specific to the type of light controller.
        """
        pass

    @abstractmethod
    def set_color(self, color):
        """
        Abstract method to set the color of the light(s).

        Args:
            color (str): The color to set for the light(s), specified as a string or other format.
        """
        pass

    @abstractmethod
    def frame(self, time, corners):
        pass
