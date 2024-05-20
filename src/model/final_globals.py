# coding=utf-8
"""Globals for whole Project"""
from abc import ABC


class FinalGlobals(ABC):
    """class for Globals of the whole Project"""

    _screen_width, _screen_height = (0, 0)

    @staticmethod
    def get_screen_width():
        """get screen width"""
        return FinalGlobals._screen_width

    @staticmethod
    def set_screen_width(screen_width: int):
        """set screen width"""
        FinalGlobals._screen_width = screen_width

    @staticmethod
    def get_screen_height():
        """get screen height"""
        return FinalGlobals._screen_height

    @staticmethod
    def set_screen_height(screen_height: int):
        """set screen height"""
        FinalGlobals._screen_height = screen_height
