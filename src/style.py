"""Styles for UI"""

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
