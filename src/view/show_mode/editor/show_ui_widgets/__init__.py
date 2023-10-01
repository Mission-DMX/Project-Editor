from model import Filter, UIWidget


def filter_to_ui_widget(filter_: Filter) -> UIWidget:
    match filter_.filter_type:
        case 0 | 1 | 2 | 3:
            # constants
            return None
        case 39 | 40 | 41 | 42 | 43:
            # Faders: Update Color
            return None
        case 44:
            # Cue Editor: play, pause, cue select, etc.
            return None
        case 50:
            # Lua Widget: query for all data types?
            return None
        case _:
            return None
