# coding=utf-8
"""GUI and control elements for the software."""

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QSplashScreen
    app = QApplication([])
    from PySide6.QtGui import QPixmap

    splashscreen = QSplashScreen(QPixmap("resources/splash.png"))
    splashscreen.show()
    splashscreen.raise_()
    app.processEvents()

    version_string = "Error reading version."
    with open("resources/version.txt", "r") as f:
        try:
            version_string = "Version: " + f.read().replace('\n', '').strip()
        except:
            pass
    from PySide6.QtGui import QColor
    from PySide6.QtCore import Qt
    splashscreen.showMessage(version_string, alignment=Qt.AlignmentFlag.AlignCenter, color=QColor.fromRgb(125, 125, 125))
    app.processEvents()

    import atexit
    import json
    import logging.config
    import logging.handlers
    import pathlib
    import sys

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

    def setup_asyncio():
        # Warning: while this change is important, the feature is yet a technical preview in pyside6.6 and the
        #  API may change. The functionality however will stay in place.
        import asyncio
        from PySide6.QtAsyncio import QAsyncioEventLoopPolicy
        asyncio.set_event_loop_policy(QAsyncioEventLoopPolicy())


    def main(app: QApplication):
        """Startup"""
        setup_logging()
        logging.basicConfig(level="INFO")
        setup_asyncio()

        app.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)

        width, height = app.primaryScreen().size().toTuple()
        FinalGlobals.set_screen_width(width)
        FinalGlobals.set_screen_height(height)
        app.setStyleSheet(Style.APP)
        JoystickHandler()

        # TODO we should parse the global application settings and recent project files here
        # TODO show a dialog asking the user to create a new show file or open a recent one
        # TODO pass the show file to be loaded as a parameter to the constructor of main window.
        # TODO pass "" if a new one should be created
        # TODO open a new MainWindow if the user clicks new from the window menu
        widget = MainWindow()
        widget.showMaximized()
        splashscreen.finish(widget)

        cli_server = RemoteCLIServer(widget.show_configuration, widget._fish_connector)
        return_code = app.exec()
        cli_server.stop()
        sys.exit(return_code)

    # Only start if __main__
    main(app)
