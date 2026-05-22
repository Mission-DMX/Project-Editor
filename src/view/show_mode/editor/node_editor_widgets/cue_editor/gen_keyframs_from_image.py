from __future__ import annotations

from typing import TYPE_CHECKING

from model.filter_data.cues.cue import KeyFrame, Cue

if TYPE_CHECKING:
    from model.media_assets.image import AbstractImageAsset


def generate_keyframes_from_image(asset: AbstractImageAsset, columns_first: bool, c: Cue) -> list[KeyFrame]:
    """Extract color values from image asset pixels.

    This will fill in the provided channels for the key frame.
    Non-color channels will be populated with their previous value or 0.

    Args:
        asset: The asset to extract the pixels from.
        columns_first: If true, the pixels will be extracted columns by rows. If false: rows by columns.
        c: The cue to extract previous values from and to insert the key frames into.

    """
    # TODO check if asset is image
    # TODO check number of accepted color channels
    # TODO raise error if #color channels != #pixels
    # TODO for each channel: if type == color: apply next pixel else get previous value or 0
    pass