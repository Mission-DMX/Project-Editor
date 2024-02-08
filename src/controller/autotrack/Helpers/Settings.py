from controller.autotrack.Calibration.MappingCalibration import MappingCalibration
from controller.autotrack.LightController import LightController


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
        self._crop: tuple[int, int, int, int] = (0, 0, 0, 0)
        self._lights: LightController | None = None
        self.settings = {
            "confidence_threshold": "0.25",
            "Setting2": None,
            # Add more settings as needed
        }
        self._map: MappingCalibration | None = None
        self._next_frame = None

    @property
    def crop(self) -> tuple[int, int, int, int]:
        """
        Get or set the crop settings as a tuple (x1, x2, y1, y2).

        Returns:
            tuple: A tuple representing the crop settings (x1, x2, y1, y2).
        """
        return self._crop

    @property
    def lights(self) -> LightController | None:
        if self._lights is None:
            self._lights = None
        return self._lights

    @crop.setter
    def crop(self, value: tuple[int, int, int, int]):
        """
        Set the crop settings.

        Args:
            value (tuple): A tuple representing the crop settings (x1, x2, y1, y2).
        """
        self._crop = value

    @property
    def map(self) -> MappingCalibration | None:
        return self._map

    @map.setter
    def map(self, value: MappingCalibration):
        self._map = value

    @property
    def next_frame(self):
        return self._next_frame

    @next_frame.setter
    def next_frame(self, value):
        self._next_frame = value
