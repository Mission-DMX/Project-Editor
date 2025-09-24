"""Module contains MediaType enum."""

from enum import Enum


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

    @classmethod
    def all_values(cls) -> "list[MediaType]":
        """Return a list of all possible media types."""
        return [MediaType.TEXT, MediaType.IMAGE, MediaType.VIDEO, MediaType.AUDIO, MediaType.MODEL_3D]
