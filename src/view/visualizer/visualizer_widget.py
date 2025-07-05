import logging, os
from PySide6 import QtWidgets, QtCore
from utility import resource_path
from model.stage import StageConfig
from view.visualizer.stage_gl_widget import Stage3DWidget
from view.visualizer.stage_editor_widget import StageEditorWidget

logger = logging.getLogger(__file__)


class StageVisualizerWidget(QtWidgets.QSplitter):

    def __init__(self, board_configuration, broadcaster, parent=None):
        super().__init__(parent)
        self._broadcaster = broadcaster
        self._board_configuration = board_configuration

        self.setOrientation(QtCore.Qt.Orientation.Horizontal)

        stage_yaml_path = resource_path(os.path.join("resources", "data", "stage.yaml"))
        self._stage_config = StageConfig(stage_yaml_path)

        self._gl_widget = Stage3DWidget(self._stage_config, parent=self)
        self._editor_widget = StageEditorWidget(self._stage_config, parent=self)
        self.addWidget(self._gl_widget)
        self.addWidget(self._editor_widget)

        self._editor_widget.addObjectRequested.connect(self._on_add_object)
        self._editor_widget.removeObjectRequested.connect(self._on_remove_object)
        self._editor_widget.objectChanged.connect(self._on_object_changed)

    def _on_add_object(self, object_type: type):
        new_id = self._stage_config.get_new_id(object_type.__name__.lower())
        new_obj = object_type(new_id)

        self._stage_config.add_object(new_obj)
        self._editor_widget.add_object_to_list(new_obj)

        self._gl_widget.makeCurrent()
        self._gl_widget.load_object(new_obj)
        self._gl_widget.doneCurrent()
        self._gl_widget.update()

        self._stage_config.save()
        logger.info("Added new object: %s (type: %s)", new_obj.id, object_type)

    def _on_remove_object(self, object_id: str):
        obj = self._stage_config.remove_object(object_id)
        if obj:
            self._editor_widget.remove_object_from_list(object_id)
            self._gl_widget.makeCurrent()
            self._gl_widget.remove_object(obj)
            self._gl_widget.doneCurrent()
            self._gl_widget.update()

            self._stage_config.save()
            logger.info("Removed object: %s", object_id)
        else:
            logger.warning("Object with id %s not found for removal", object_id)

    def _on_object_changed(self, object_id: str):

        self._gl_widget.update()
        self._stage_config.save()
        logger.info("Updated object transform: %s", object_id)
