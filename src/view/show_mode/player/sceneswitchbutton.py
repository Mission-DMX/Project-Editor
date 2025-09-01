"""Scene widget for scene player."""

from PySide6.QtWidgets import QPushButton, QWidget

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

    def __init__(self, scene: Scene, parent: QWidget = None) -> None:
        """Initialize button using scene to switch to as well as parent Qt widget."""
        super().__init__(parent)
        if SceneSwitchButton._STYLE_NOT_ACTIVE is None:
            SceneSwitchButton._STYLE_NOT_ACTIVE = self.styleSheet()
        self._scene = scene
        self.clicked.connect(self._clicked)
        self.setFixedSize(self.width, self.height)
        self.setText(self._scene.human_readable_name)
        b = Broadcaster()
        b.active_scene_switched.connect(self._active_scene_switched)

    def _clicked(self) -> None:
        """Handle behavior when the scene button is clicked."""
        # transmit_to_fish(self._scene.board_configuration)
        self._scene.board_configuration.broadcaster.change_active_scene.emit(self._scene)
        # FIXME: Incorrect switching between scenes?

    def _active_scene_switched(self, new_scene_id: int) -> None:
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
