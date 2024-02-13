# coding=utf-8
"""Starts a listener for the joystick"""

import pyjoystick
from pyjoystick.sdl2 import run_event_loop, Key

from controller.cli.joystick_enum import JoystickList
from model import Broadcaster

class JoystickHandler:

    @staticmethod
    def reformat(key):
        if key.keytype == Key.AXIS:
            tilt = False
            match key.number:
                case 0:
                    jstick = JoystickList.Gamepad_Left
                    tilt = True
                case 1:
                    jstick = JoystickList.Gamepad_Left
                case 2:
                    jstick = JoystickList.Gamepad_Right
                    tilt = True
                case 3:
                    jstick = JoystickList.Gamepad_Right
                case _:
                    return
            (Broadcaster()).handle_joystick_event.emit(jstick, key.value, tilt)



    def __new__(cls):
        mngr = pyjoystick.ThreadEventManager(event_loop=run_event_loop,
                                             handle_key_event=lambda key: cls.reformat(key)
                                             )
        mngr.start()