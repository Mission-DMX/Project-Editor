from abc import ABC, abstractmethod

from PySide6.QtGui import QPixmap

from model.media_assets.factory_hint import AssetFactoryObjectHint
from model.media_assets.media_type import MediaType
from model.media_assets.registry import register


class MediaAsset(ABC):
    # TODO write doc

    def __init__(self, uuid: str) -> None:
        """Construct a base MediaAsset.

        This method also automatically registers the asset.

        Args:
            uuid (str): The UUID of the asset.
        """
        self._id = uuid
        register(self, uuid)

    @abstractmethod
    def get_type(self) -> MediaType:
        """This method must be implemented to return the media asset type.

        Furthermore, this method must be working prior to the constructor being finished.
        """
        raise NotImplementedError

    @property
    def id(self) -> str:
        """Get the UUID of this asset.

        Returns:
            str: The UUID of this asset.
        """
        return self._id

    @abstractmethod
    def get_thumbnail(self) -> QPixmap:
        """Get the thumbnail of this asset.

        The pixmap has a size 64x64 pixels.

        Returns:
            QPixmap: The thumbnail of this asset."""
        raise NotImplementedError

    @abstractmethod
    def serialize_settings(self) -> str:
        """Serialize the asset properties into a string"""
        raise NotImplementedError

    @abstractmethod
    def get_factory_object_hint(self) -> AssetFactoryObjectHint:
        """This method needs to return the type that the asset factory should load upon show file loading."""
        raise NotImplementedError
