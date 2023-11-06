import Lights
from Lights.ArtNet import ArtNet


class Settings:
    """
    The `Settings` class manages application settings.

    Attributes:
        _crop (tuple): A tuple representing the crop settings (x1, x2, y1, y2).
        settings (dict): A dictionary of various application settings.

    Methods:
        - `__init__()`: Initialize the `Settings` class with default values.
        - `crop`: Get or set the crop settings as a tuple (x1, x2, y1, y2).
    """

    def __init__(self):
        """
        Initialize the `Settings` class with default values.
        """
        self._crop = (0, 0, 0, 0)
        self._lights = None
        self.settings = {
            "confidence_threshold": "0.25",
            "Setting2": None,
            # Add more settings as needed
        }
        self._map = None
        self._next_frame = None

    @property
    def crop(self):
        """
        Get or set the crop settings as a tuple (x1, x2, y1, y2).

        Returns:
            tuple: A tuple representing the crop settings (x1, x2, y1, y2).
        """
        return self._crop

    @property
    def lights(self):
        if self._lights is None:
            self._lights = ArtNet()
        return self._lights

    @crop.setter
    def crop(self, value):
        """
        Set the crop settings.

        Args:
            value (tuple): A tuple representing the crop settings (x1, x2, y1, y2).
        """
        self._crop = value

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, value):
        self._map = value

    @property
    def next_frame(self):
        return self._next_frame

    @next_frame.setter
    def next_frame(self, value):
        self._next_frame = value
