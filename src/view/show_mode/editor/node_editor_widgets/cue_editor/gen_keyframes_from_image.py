"""Contains generate_keyframes_from_image method."""

from __future__ import annotations

from typing import TYPE_CHECKING

from model import DataType
from model.color_hsi import ColorHSI
from model.filter_data.cues.cue import Cue, KeyFrame, StateColor, StateDouble, StateEightBit, StateSixteenBit
from model.media_assets.image import AbstractImageAsset

if TYPE_CHECKING:
    from PySide6.QtGui import QColor

    from model.filter_data.cues.cue import State


def _state_matches_channel(state: State, data_type: DataType) -> bool:
    """Check whether a state is compatible with a channel of the given data type."""
    match data_type:
        case DataType.DT_COLOR:
            return isinstance(state, StateColor)
        case DataType.DT_8_BIT:
            return isinstance(state, StateEightBit)
        case DataType.DT_16_BIT:
            return isinstance(state, StateSixteenBit)
        case DataType.DT_DOUBLE:
            return isinstance(state, StateDouble)
        case _:
            return False


def generate_keyframes_from_image(
    asset: AbstractImageAsset,
    columns_first: bool,
    timestamp: float,
    break_point: int,
    transition_types: list[str],
    c: Cue,
) -> None:
    """Extract color values from image asset pixels.

    This will fill in the provided channels for the key frame.
    Non-color channels will be populated with their previous value or 0.

    Args:
        asset: The asset to extract the pixels from.
        columns_first: If true, the pixels will be extracted columns by rows. If false: rows by columns.
        timestamp: The timestamp to insert the keyframe to.
        break_point: After this many pixels, the pixel cursor advances to the next column or row (depending on
                     columns_first). If an invalid number is supplied (for example 0), it will break after the asset
                     height (row).
        transition_types: For each channel, specifies the transition type from the last key frame.
        c: The cue to extract previous values from and to insert the key frames into.

    """
    if not isinstance(asset, AbstractImageAsset):
        raise ValueError(f"Asset must be an image asset. Got: {type(asset)}")
    if len(c.channels) != len(transition_types):
        raise ValueError("Expected a transition type for each channel.")
    number_of_color_channels = 0
    for _, data_type in c.channels:
        if data_type == DataType.DT_COLOR:
            number_of_color_channels += 1
    image = asset.get_image_for_ui()
    image_size = image.size()
    image_width = image_size.width()
    image_height = image_size.height()
    if number_of_color_channels > image_width * image_height:
        raise ValueError("Number of color channels must not be greater than asset pixel count.")
    if columns_first:
        if break_point < 1 or break_point >= image_height:
            break_point = image_height
    else:
        if break_point < 1 or break_point >= image_width:
            break_point = image_width
    x: int = 0
    y: int = 0
    break_point_offset: int = 0
    kf = KeyFrame(c)
    kf.timestamp = timestamp
    last_frame: KeyFrame | None = c.get_keyframe_before(timestamp)
    for i, channel in enumerate(c.channels):
        _channel_name, data_type = channel
        if data_type == DataType.DT_COLOR:
            pixel: QColor = image.pixelColor(x, y)
            state = StateColor(transition_types[i])
            state.color = ColorHSI.from_qt_color(pixel)
            if columns_first:
                y += 1
                if (y - break_point_offset) >= break_point or y >= image_height:
                    y = break_point_offset
                    x += 1
                if x >= image_width:
                    x = 0
                    break_point_offset += break_point
                    if break_point_offset >= image_height:
                        break_point_offset = 0
                    y = break_point_offset
            else:
                x += 1
                if (x - break_point_offset) >= break_point or x >= image_width:
                    x = break_point_offset
                    y += 1
                if y >= image_height:
                    y = 0
                    break_point_offset += break_point
                    if break_point_offset >= image_width:
                        break_point_offset = 0
                    x = break_point_offset
            kf.append_state(state)
        else:
            if (
                last_frame is not None
                and i < last_frame.state_count
                and _state_matches_channel(last_frame.state_at(i), data_type)
            ):
                state = last_frame.state_at(i).copy()
                state.transition = transition_types[i]
                kf.append_state(state)
            else:
                match data_type:
                    case DataType.DT_8_BIT:
                        state = StateEightBit(transition_types[i])
                    case DataType.DT_16_BIT:
                        state = StateSixteenBit(transition_types[i])
                    case DataType.DT_DOUBLE:
                        state = StateDouble(transition_types[i])
                    case _:
                        raise NotImplementedError(f"Data type {data_type} not implemented for initialization yet.")
                kf.append_state(state)

    c.insert_frame(kf)
