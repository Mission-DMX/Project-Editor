from PySide6.QtWidgets import QInputDialog, QWidget

from model import BoardConfiguration, Scene


def add_scene_to_show(parent: QWidget | None, config: BoardConfiguration) -> Scene | None:
    scene_name, ok_button_pressed = QInputDialog.getText(parent, "Create a new scene", "Scene name")
    if ok_button_pressed:
        scene = Scene(scene_id=len(config.scenes),
                      human_readable_name=scene_name,
                      board_configuration=config)
        config.broadcaster.scene_created.emit(scene)
        return scene
    return None
