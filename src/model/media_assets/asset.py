"""Module contains abstract asset class."""

import os
from abc import ABC, abstractmethod
from logging import getLogger
from uuid import uuid4

from PySide6.QtGui import QPixmap

from model.media_assets.factory_hint import AssetFactoryObjectHint
from model.media_assets.media_type import MediaType
from model.media_assets.registry import register

logger = getLogger(__name__)

GLOBAL_ASSET_FOLDER = "/usr/local/share/missionDMX"
try:
    if not os.path.exists(GLOBAL_ASSET_FOLDER):
        os.mkdir(GLOBAL_ASSET_FOLDER)
except OSError as e:
    logger.error("Failed to create global asset folder: %s", str(e))


class MediaAsset(ABC):
    """Abstract Asset class.

    This class takes care of common functionality, such as, registration of asset being created, properties for ID and
    type as well as methods for show file serialization requirements.
    """

    def __init__(self, uuid: str = "") -> None:
        """Construct a base MediaAsset.

        This method also automatically registers the asset.

        Args:
            uuid (str): The UUID of the asset. If an empty string is provided, a random one will be generated.

        """
        self._id = uuid if len(uuid) > 0 else str(uuid4())
        register(self, self._id)

    @abstractmethod
    def get_type(self) -> MediaType:
        """Method must be implemented to return the media asset type.

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
        """Serialize the asset properties into a string."""
        raise NotImplementedError

    @abstractmethod
    def get_factory_object_hint(self) -> AssetFactoryObjectHint:
        """Method needs to return the type that the asset factory should load upon show file loading."""
        raise NotImplementedError
