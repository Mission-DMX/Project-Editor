"""Starts a listener for the joystick"""
from __future__ import annotations

from typing import Self

import pyjoystick
from pyjoystick.sdl2 import Key, run_event_loop

from controller.joystick.joystick_enum import JoystickList
from model import Broadcaster


class JoystickHandler:
    joystick_map = {}

    @staticmethod
    def reformat(key: Key) -> None:
        """Rename the input keys.
        :param key: The input event to rename"""
        if key.keytype == Key.AXIS:
            tilt = False
            match key.number:
                case 0:
                    joystick = JoystickList.GAMEPAD_LEFT
                case 1:
                    joystick = JoystickList.GAMEPAD_LEFT
                    tilt = True
                case 2:
                    joystick = JoystickList.GAMEPAD_RIGHT
                    key.value = key.value * 2 - 1  # Todo: check if my gamepad only for my laptop is broken
                    if 0.2 > key.value > -0.4:
                        key.value = 0
                case 3:
                    joystick = JoystickList.GAMEPAD_RIGHT
                    tilt = True
                case _:
                    return
            (Broadcaster()).handle_joystick_event.emit(joystick, key.value, tilt)

    def __new__(cls) -> Self:
        """Connect a joystick and setup the key bindings"""
        mngr = pyjoystick.ThreadEventManager(event_loop=run_event_loop,
                                             handle_key_event=lambda key: cls.reformat(key),
                                             )
        cls.joystick_map["No Joystick"] = JoystickList.NO_JOYSTICK
        cls.joystick_map["Gamepad Left"] = JoystickList.GAMEPAD_LEFT
        cls.joystick_map["Gamepad Right"] = JoystickList.GAMEPAD_RIGHT
        cls.joystick_map["Joystick"] = JoystickList.JOYSTICK
        mngr.start()
