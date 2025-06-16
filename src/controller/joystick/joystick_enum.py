# coding=utf-8
"""List of all joysticks"""
from enum import Enum


class JoystickList(Enum):
    """Joysticks available"""
    NO_JOYSTICK = 1
    EVERY_JOYSTICK = 2
    GAMEPAD_LEFT = 3
    GAMEPAD_RIGHT = 4
    JOYSTICK = 5
