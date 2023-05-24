# coding=utf-8
"""GUI and control elements for the software."""

import logging
import sys

from PySide6 import QtWidgets

from Style import Style
from view.main_window import MainWindow


def main():
    """Startup"""
    logging.basicConfig(encoding='utf-8', level=logging.INFO)
    from cli.remote_control_port import RemoteCLIServer

    cli_server = RemoteCLIServer()
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    screen_width = app.primaryScreen().size().width()
    screen_height = app.primaryScreen().size().height()
    widget = MainWindow()
    widget.showMaximized()

    return_code = app.exec()
    cli_server.stop()
    sys.exit(return_code)


if __name__ == "__main__":
    """Only start if __main__"""
    main()
