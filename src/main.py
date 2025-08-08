"""GUI and control elements for the software."""

if __name__ == "__main__":
    import os

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QSplashScreen

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    app = QApplication([])
    from PySide6.QtGui import QPixmap

    from utility import resource_path

    splashscreen = QSplashScreen(QPixmap(resource_path(os.path.join("resources", "splash.png"))))
    splashscreen.show()
    splashscreen.raise_()

    with open(resource_path(os.path.join("resources", "pyproject.toml")), "r", encoding="UTF-8") as f:
        import tomlkit

        data = tomlkit.load(f)
    version_string = f"Version: {data['project']['version']}"

    app.processEvents()
    app.setApplicationName(data["project"]["name"])
    app.setApplicationDisplayName(data["tool"]["missionDMX"]["display-name"])
    app.setOrganizationName(data["tool"]["missionDMX"]["organization"]["name"])
    app.setOrganizationDomain(data["tool"]["missionDMX"]["organization"]["domain"])
    app.setDesktopSettingsAware(True)
    from PySide6.QtGui import QIcon

    app.setWindowIcon(QIcon(resource_path(os.path.join("resources", "app-icon.png"))))

    from PySide6.QtGui import QColor, QPalette

    splashscreen.showMessage(
        version_string, alignment=Qt.AlignmentFlag.AlignCenter, color=QColor.fromRgb(125, 125, 125)
    )
    app.processEvents()

    import atexit
    import json
    import logging.config
    import logging.handlers
    import pathlib
    import sys

    from PySide6.QtCore import QEventLoop

    import style
    from controller.cli.remote_control_port import RemoteCLIServer
    from controller.joystick.joystick_handling import JoystickHandler
    from gl_init import opengl_context_init
    from model.final_globals import FinalGlobals
    from view.main_window import MainWindow

    logger = logging.getLogger("Project-Editor")

    def setup_logging() -> None:
        """Read logging from config file and set up the logger"""
        config_file = resource_path(pathlib.Path(os.path.join("configs", "logging.json")))
        with open(config_file, "r", encoding="utf-8") as f_in:
            config = json.load(f_in)

        logging.config.dictConfig(config)
        queue_handler = logging.getHandlerByName("queue_handler")
        if queue_handler is not None:
            queue_handler.listener.start()
            atexit.register(queue_handler.listener.stop)

    def setup_asyncio() -> None:
        # Warning: while this change is important, the feature is yet a technical preview in pyside6.6 and the
        #  API may change. The functionality however will stay in place.
        import asyncio

        from PySide6.QtAsyncio import QAsyncioEventLoopPolicy

        asyncio.set_event_loop_policy(QAsyncioEventLoopPolicy())

    def set_dark_theme(application: QApplication) -> None:
        """Set default dark theme"""
        application.setStyle("Fusion")
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(42, 42, 42))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(40, 14, 237).lighter())
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(150, 150, 150))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(150, 150, 150))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(150, 150, 150))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(100, 100, 100))

        application.setPalette(dark_palette)

    def main(application: QApplication) -> None:
        """Startup"""
        setup_logging()
        logging.basicConfig(level="INFO")
        opengl_context_init()
        setup_asyncio()

        width, height = application.primaryScreen().size().toTuple()
        FinalGlobals.set_screen_width(width)
        FinalGlobals.set_screen_height(height)
        set_dark_theme(application)
        application.setStyleSheet(style.APP)
        JoystickHandler()

        # TODO we should parse the global application settings and recent project files here
        # TODO show a dialog asking the user to create a new show file or open a recent one
        # TODO open a new MainWindow if the user clicks new from the window menu
        widget = MainWindow()
        widget.showMaximized()

        cli_server = RemoteCLIServer(widget.show_configuration, widget.fish_connector)
        application.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
        if len(sys.argv) > 1:
            show_file_path = sys.argv[1]
            if os.path.isfile(show_file_path):
                from controller.file.read import read_document

                read_document(show_file_path, widget.show_configuration)
                application.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
            else:
                logger.warning("Failed to open show file '%s' as it does not seam to be a file.", show_file_path)
        splashscreen.finish(widget)
        return_code = application.exec()
        cli_server.stop()
        sys.exit(return_code)

    # Only start if __main__
    main(app)
