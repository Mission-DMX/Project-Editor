# coding=utf-8
"""GUI and control elements for the software."""

import logging
import sys

from PySide6 import QtWidgets

from Style import Style
from controller.cli.joystick_handling import JoystickHandler
from view.main_window import MainWindow
from controller.cli.remote_control_port import RemoteCLIServer


def main():
    """Startup"""
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    cli_server = RemoteCLIServer()
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    JoystickHandler()
    widget = MainWindow()
    widget.showMaximized()

    return_code = app.exec()
    cli_server.stop()
    sys.exit(return_code)


if __name__ == "__main__":
    # Only start if __main__
    main()
