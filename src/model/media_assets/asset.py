from abc import ABC, abstractmethod

from model.media_assets.media_type import MediaType


class MediaAsset(ABC):
    # TODO write doc
    # TODO write constructor that registers itself

    @abstractmethod
    def get_type(self) -> MediaType:
        """This method must be implemented to return the media asset type."""
        raise NotImplementedError()
