from __future__ import annotations

from typing import TYPE_CHECKING

from model.filter_data.cues.cue import KeyFrame

if TYPE_CHECKING:
    from model.media_assets.image import AbstractImageAsset


def generate_keyframes_from_image(asset: AbstractImageAsset) -> list[KeyFrame]:
    # TODO check if asset is image
    # TODO check number of accepted color channels
    # TODO raise error if #color channels != #pixels
    # TODO for each channel: if type == color: apply next pixel else get previous value or 0
    pass