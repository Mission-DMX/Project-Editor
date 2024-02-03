# coding=utf-8
"""Starts a listener for the joystick"""
import pyjoystick
from pyjoystick.sdl2 import run_event_loop

from model import Broadcaster

class JoystickHandler:
    def __new__(cls):
        mngr = pyjoystick.ThreadEventManager(event_loop=run_event_loop,
                                             handle_key_event=lambda key: (Broadcaster()).handle_joystick_event.emit(key)
                                             )
        mngr.start()