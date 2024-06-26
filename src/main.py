# coding=utf-8
"""GUI and control elements for the software."""
import atexit
import json
import logging.config
import logging.handlers
import pathlib
import sys

from PySide6 import QtWidgets

from controller.cli.remote_control_port import RemoteCLIServer
from controller.joystick.joystick_handling import JoystickHandler
from model.final_globals import FinalGlobals
from Style import Style
from view.main_window import MainWindow

logger = logging.getLogger("Project-Editor")


def setup_logging():
    """read logging from config file and set up the logger"""
    config_file = pathlib.Path("../configs/logging.json")
    with open(config_file, encoding="utf-8") as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)


def main():
    """Startup"""
    setup_logging()
    logging.basicConfig(level="INFO")

    app = QtWidgets.QApplication([])
    width, height = app.primaryScreen().size().toTuple()
    FinalGlobals.set_screen_width(width)
    FinalGlobals.set_screen_height(height)
    app.setStyleSheet(Style.APP)
    JoystickHandler()
    widget = MainWindow()
    widget.showMaximized()

    cli_server = RemoteCLIServer(widget.show_configuration, widget._fish_connector)
    return_code = app.exec()
    cli_server.stop()
    sys.exit(return_code)


if __name__ == "__main__":
    # Only start if __main__
    main()
