"""Module contains MediaType enum."""
import os
from enum import Enum

from PySide6.QtGui import QIcon

from utility import resource_path

_ICON_TEXT = QIcon(resource_path(os.path.join("resources", "icons", "media_text.svg")))
_ICON_IMAGE = QIcon(resource_path(os.path.join("resources", "icons", "media_image.png")))
_ICON_VIDEO = QIcon(resource_path(os.path.join("resources", "icons", "media_video.png")))
_ICON_AUDIO = QIcon(resource_path(os.path.join("resources", "icons", "media_audio.png")))
_ICON_3D = QIcon(resource_path(os.path.join("resources", "icons", "media_3d.png")))
_ICON_UNKNOWN = QIcon(resource_path(os.path.join("resources", "icons", "media_unknown.png")))


class MediaType(Enum):
    """Enum provides the distinguished media types."""

    TEXT = 0
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3
    MODEL_3D = 4

    def get_padded_description(self) -> str:
        """Get a human-readable description of the type padded to 5 chars."""
        match self:
            case MediaType.TEXT:
                return "Text "
            case MediaType.IMAGE:
                return "Image"
            case MediaType.VIDEO:
                return "Video"
            case MediaType.AUDIO:
                return "Audio"
            case MediaType.MODEL_3D:
                return "3D   "
            case _:
                return "UNKN."

    def get_long_description(self) -> str:
        """Get a human-readable long description of the type."""
        match self:
            case MediaType.TEXT:
                return "Text"
            case MediaType.IMAGE:
                return "Image"
            case MediaType.VIDEO:
                return "Video"
            case MediaType.AUDIO:
                return "Audio"
            case MediaType.MODEL_3D:
                return "3D"
            case _:
                return "Unknown Asset Type"

    def get_qt_hint_icon(self) -> QIcon:
        """Return a QIcon representing the media type."""
        match self:
            case MediaType.TEXT:
                return _ICON_TEXT
            case MediaType.IMAGE:
                return _ICON_IMAGE
            case MediaType.VIDEO:
                return _ICON_VIDEO
            case MediaType.AUDIO:
                return _ICON_AUDIO
            case MediaType.MODEL_3D:
                return _ICON_3D
            case _:
                return _ICON_UNKNOWN

    @classmethod
    def all_values(cls) -> "list[MediaType]":
        """Return a list of all possible media types."""
        return [MediaType.TEXT, MediaType.IMAGE, MediaType.VIDEO, MediaType.AUDIO, MediaType.MODEL_3D]
