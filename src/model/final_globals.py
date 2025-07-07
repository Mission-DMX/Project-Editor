"""Globals for whole Project"""


class FinalGlobals:
    """class for Globals of the whole Project"""

    _screen_width: int = 0
    _screen_height: int = 0

    @staticmethod
    def get_screen_width() -> int:
        """get screen width"""
        return FinalGlobals._screen_width

    @staticmethod
    def set_screen_width(screen_width: int):
        """set screen width"""
        FinalGlobals._screen_width = screen_width

    @staticmethod
    def get_screen_height() -> int:
        """get screen height"""
        return FinalGlobals._screen_height

    @staticmethod
    def set_screen_height(screen_height: int):
        """set screen height"""
        FinalGlobals._screen_height = screen_height
