"""Styles for the UI."""

from pydantic import BaseModel, ConfigDict
from PySide6.QtGui import QFont


class _TextItem(BaseModel):
    x: int
    y: int
    font: QFont

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)


class _ICON(BaseModel):
    x: int
    y: int
    width: int
    height: int


class _Parts(BaseModel):
    channel_id: _TextItem
    fixture_name: _TextItem
    fixture_channel_name: _TextItem
    fixture_name_on_stage: _TextItem
    dmx_value: _TextItem
    dmx_trend: _TextItem
    dmx_trend_icon: _ICON
    model_config = ConfigDict(frozen=True)


class _PatchItem(BaseModel):
    width: int
    height: int
    margin: int
    padding: int
    parts: _Parts

    model_config = ConfigDict(frozen=True)


APP = ""

WIDGET = ""

SCROLL = """
QScrollArea {
    border-style: outset;
    border-width: 1px;
    border-color: black;
}
"""

BUTTON = """
QPushButton {
    border-style: outset;
    border-width: 1px;
    border-color: gray;
    border-radius: 5px;
}
"""

ACTIVE_BUTTON = """
QPushButton {
    background-color: rgba(169, 222, 245, 1);
    border-radius: 5px;
}
"""

SLIDER = ""

LABEL_OKAY = "background-color: rgba(0, 255, 0, 1);"
LABEL_WARN = "background-color: rgba(255, 127, 0, 1);"
LABEL_ERROR = "background-color: rgba(255, 0, 0, 1);"

PATCH = "margin: 0px; padding: 1px; color: black;"

PATCH_ITEM = _PatchItem(
    width=100,
    height=100,
    margin=1,
    padding=5,
    parts=_Parts(
        channel_id=_TextItem(x=0, y=15, font=QFont("Arial", 13)),
        fixture_name=_TextItem(x=0, y=30, font=QFont("Arial", 10)),
        fixture_channel_name=_TextItem(x=0, y=45, font=QFont("Arial", 10)),
        fixture_name_on_stage=_TextItem(x=0, y=60, font=QFont("Arial", 10)),
        dmx_value=_TextItem(x=0, y=75, font=QFont("Arial", 13)),
        dmx_trend=_TextItem(x=20, y=90, font=QFont("Arial", 10)),
        dmx_trend_icon=_ICON(x=0, y=80, width=10, height=10),
    ),
)

CHANNEL_STYLE_8BIT = """
   background-color: #202020;
   color: #DDDDDD;
   border-radius: 5px;
   padding: 3px;
   """

CHANNEL_STYLE_16BIT = """
   background-color: #202020;
   color: #EEEEEE;
   border-radius: 5px;
   padding: 3px;
   """

CHANNEL_STYLE_FLOAT = """
   background-color: #202020;
   color: #FFFFFF;
   border-radius: 5px;
   padding: 3px;
   """

CHANNEL_STYLE_COLOR = """
   background-color: #202020;
   color: #10AA10;
   border-radius: 5px;
   padding: 3px;
   """
