"""Application settings."""

from logging import getLogger
from typing import TYPE_CHECKING

from controller.autotrack.Calibration.MappingCalibration import MappingCalibration
from controller.autotrack.LightController import LightController

if TYPE_CHECKING:
    from model.virtual_filters.auto_tracker_filter import AutoTrackerFilter

logger = getLogger(__file__)


class AutoTrackerSettings:
    """Manages application settings.

    Attributes:
        _crop (tuple): A tuple representing the crop settings (x1, x2, y1, y2).
        settings (dict): A dictionary of various application settings.

    Methods:
        - `__init__()`: Initialize the `Settings` class with default values.
        - `crop`: Get or set the crop settings as a tuple (x1, x2, y1, y2).

    """

    def __init__(self, f: "AutoTrackerFilter"):
        """Initialize the `Settings` class with default values."""
        self._crop: tuple[int, int, int, int] = (0, 0, 0, 0)
        self._lights: LightController = f.light_controller
        self._filter: "AutoTrackerFilter" = f
        self.settings = {
            "confidence_threshold": "0.25",
            "Setting2": "",
        }
        self._map: MappingCalibration | None = None
        if self.settings.get("mapping_calibration"):
            self._map = MappingCalibration(self.settings["mapping_calibration"])
        if self.settings.get("crop"):
            self._load_crop(self.settings["crop"])
        self._next_frame = None

    @property
    def crop(self) -> tuple[int, int, int, int]:
        """Crop settings.

        Returns:
            tuple: A tuple representing the crop settings (x1, x2, y1, y2).

        """
        return self._crop

    @property
    def lights(self) -> LightController:
        """Light controller."""
        return self._lights

    @crop.setter
    def crop(self, value: tuple[int, int, int, int]):
        self._crop = value
        self._filter.filter_configurations.update(self.as_dict())

    @property
    def map(self) -> MappingCalibration | None:
        """Mapping calibration."""
        return self._map

    @map.setter
    def map(self, value: MappingCalibration):
        self._map = value
        self._filter.filter_configurations.update(self.as_dict())

    @property
    def next_frame(self):
        """Next frame."""
        return self._next_frame

    @next_frame.setter
    def next_frame(self, value):
        self._next_frame = value
        # This does not need to be saved to filter preferences as it is just the last image that was captured.
        # TODO perform a proper refactor to remove this from settings

    def as_dict(self):
        """Convert settings to dict."""
        return {
            "confidence_threshold": "0.25",
            "Setting2": "",
            "crop": str(self._crop),
            "mapping_calibration": str(self._map),
        }

    def _load_crop(self, cs: str):
        """Parse the provided definition and store it inside the cropping definition.

        Args:
            cs: The string representation of the cropping information to parse.

        """
        cx_args = cs.replace("(", "").replace(")", "").split(", ")
        self.crop = (int(cx_args[0]), int(cx_args[1]), int(cx_args[2]), int(cx_args[3]))
