"""Globals for whole Project"""


class FinalGlobals:
    """class for Globals of the whole Project"""

    _screen_width: int = 0
    _screen_height: int = 0

    @staticmethod
    def get_screen_width() -> int:
        """Get screen width"""
        return FinalGlobals._screen_width

    @staticmethod
    def set_screen_width(screen_width: int) -> None:
        """Set screen width"""
        FinalGlobals._screen_width = screen_width

    @staticmethod
    def get_screen_height() -> int:
        """Get screen height"""
        return FinalGlobals._screen_height

    @staticmethod
    def set_screen_height(screen_height: int) -> None:
        """Set screen height"""
        FinalGlobals._screen_height = screen_height
