from enum import Enum


class AssetFactoryObjectHint(Enum):
    """Types that the AssetFactory may load on show file loading."""
    IMAGE_EXTERNAL_FILE = "images.file"
    IMAGE_EMBEDDED_IN_SHOWFILE = "images.embedded"
