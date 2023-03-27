from enum import Enum


class Style(str, Enum):
    """Styles used throughout the app.

    TODO Find good styles

    Attributes:
        APP: General style settings for the entire application
        WIDGET: General style settings for all widget
        SCROLL: General style settings for a scroll area
        BUTTON: General style settings for a button.
        ACTIVE_BUTTON: General style settings for an active button.
        SLIDER: General style settings for a slider.
    """
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
        border-style: outset;
        border-width: 1px;
        border-color: gray;
        border-radius : 5;
    """
    ACTIVE_BUTTON = "background-color : rgba(169,222,245,1); border-radius : 5;"
    SLIDER = ""