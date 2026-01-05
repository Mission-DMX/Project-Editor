"""Style for UI."""

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

LABEL_STYLE_BULLET = """
   background-color: #EEEEEE;
   border-radius: 5px;
   padding: 3px;
"""

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

READY_MODE_INDICATOR_STYLE = """
  background-color: #AA0000;
  border-radius: 5px;
  padding: 3px;
  color: #000000;
  text-align: center;
"""
