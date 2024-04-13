# coding=utf-8
"""List of all joysticks"""
from enum import Enum

from PySide6.QtCore import QEnum


@QEnum
class JoystickList(Enum):
    """Joysticks available"""
    NoJoystick = 1
    EveryJoystick = 2
    Gamepad_Left = 3
    Gamepad_Right = 4
    Joystick = 5
