"""Scene widget for scene player."""
from collections.abc import Callable

from PySide6.QtWidgets import QPushButton, QWidget

from controller.network import NetworkManager
from model import Broadcaster, Scene


class SceneSwitchButton(QPushButton):
    """Widget to be displayed for a scene in the show player.

    Clicking the button will transmit the board config to fish and change the active scene.
    """

    width = 100
    height = 75

    _STYLE_ACTIVE_SCENE = """
        background: #004400;
    """

    _STYLE_NOT_ACTIVE = None

    def __init__(self, scene: Scene, parent: QWidget = None, force_reload_callback: Callable | None = None) -> None:
        """Initialize button using scene to switch to as well as parent Qt widget."""
        super().__init__(parent)
        if SceneSwitchButton._STYLE_NOT_ACTIVE is None:
            SceneSwitchButton._STYLE_NOT_ACTIVE = self.styleSheet()
        self._scene = scene
        self.clicked.connect(self._clicked)
        self.setFixedSize(self.width, self.height)
        self.setText(self._scene.human_readable_name)
        self._reload_hook: Callable | None = force_reload_callback
        b = Broadcaster()
        b.active_scene_switched.connect(self._active_scene_switched)

    def _clicked(self) -> None:
        """Handle behavior when the scene button is clicked."""
        if self._scene is not None and self._scene.scene_id == NetworkManager().current_active_scene_id:
            if self._reload_hook is not None:
                self._reload_hook()
        else:
            self._scene.board_configuration.broadcaster.change_active_scene.emit(self._scene)

    def _active_scene_switched(self, new_scene_id: int) -> None:
        if not isinstance(new_scene_id, int):
            return
        if new_scene_id < 0:
            return  # Fish transmitted a scene error
        if new_scene_id == self._scene.scene_id:
            self.setChecked(True)
            self.setStyleSheet(SceneSwitchButton._STYLE_ACTIVE_SCENE)
        else:
            self.setChecked(False)
            self.setStyleSheet(SceneSwitchButton._STYLE_NOT_ACTIVE)

    @property
    def scene(self) -> Scene:
        """The scene this widget represents."""
        return self._scene
