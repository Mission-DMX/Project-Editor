# coding=utf-8
"""Starts a listener for the joystick"""

import pyjoystick
from pyjoystick.sdl2 import run_event_loop, Key

from controller.joystick.joystick_enum import JoystickList
from model import Broadcaster


class JoystickHandler:

    joystickMap = {}

    @staticmethod
    def reformat(key):
        if key.keytype == Key.AXIS:
            tilt = False
            match key.number:
                case 0:
                    joystick = JoystickList.Gamepad_Left
                case 1:
                    joystick = JoystickList.Gamepad_Left
                    tilt = True
                case 2:
                    joystick = JoystickList.Gamepad_Right
                    key.value = key.value * 2 - 1 # Todo: check if my gamepad only for my laptop is broken
                    if 0.2 > key.value > -0.4:
                        key.value = 0
                case 3:
                    joystick = JoystickList.Gamepad_Right
                    tilt = True
                case _:
                    return
            (Broadcaster()).handle_joystick_event.emit(joystick, key.value, tilt)

    def __new__(cls):
        mngr = pyjoystick.ThreadEventManager(event_loop=run_event_loop,
                                             handle_key_event=lambda key: cls.reformat(key)
                                             )
        cls.joystickMap["No Joystick"] = JoystickList.NoJoystick
        cls.joystickMap["Gamepad Left"] = JoystickList.Gamepad_Left
        cls.joystickMap["Gamepad Right"] = JoystickList.Gamepad_Right
        cls.joystickMap["Joystick"] = JoystickList.Joystick
        mngr.start()
