from abc import ABC, abstractmethod
from logging import getLogger

from PySide6.QtWidgets import QLabel

from controller.file.transmitting_to_fish import transmit_to_fish
from model import Broadcaster, DataType, Filter
from model.control_desk import BankSet, DeskColumn
from model.virtual_filters.cue_vfilter import PreviewFilter
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.cue_editor.timeline_editor import TimelineContainer

logger = getLogger(__file__)


class ExternalChannelDefinition:
    """In case we're in preview mode we need to instantiate filters for the preview based on this information.

    As I didn't want to write a tuple of the channel name, its type as well as fader source, this class provides them
    in a named fashion.
    """

    def __init__(self, data_type: DataType, name: str, associated_fader: DeskColumn, bank_set: BankSet):
        self.data_type = data_type
        self.name = name
        self.fader = associated_fader
        self.bankset = bank_set
        self.enabled = True


class PreviewEditWidget(NodeEditorFilterConfigWidget, ABC):

    def __init__(self, f: Filter | None = None):
        super().__init__()
        self._broadcaster: Broadcaster = Broadcaster()
        self._broadcaster_signals_connected = False
        self._bankset: BankSet = None

        self._timeline_container = TimelineContainer(None)
        self._timeline_container.setEnabled(False)
        self._timeline_container.transition_type = "lin"
        self._jw_zoom_mode = False

        self._filter_instance: PreviewFilter | None = f if isinstance(f, PreviewFilter) else None
        if self._filter_instance:
            self._filter_instance.associated_editor_widget = self
        else:
            logger.error("Cue editor widget received invalid filter: %s.", f)
        self._set_zoom_label_text()

    @abstractmethod
    def get_channel_list(self) -> list[ExternalChannelDefinition]:
        """
        This method needs to return the list of exposed channels. It may return a mutable list as it will be
        copied anyway

        :returns: A list of ExternalChannelDefinition objects
        """
        raise NotImplementedError()

    @property
    def channels(self) -> list[ExternalChannelDefinition]:
        return self.get_channel_list().copy()

    def _link_bankset(self):
        self._broadcaster.desk_media_rec_pressed.connect(self._rec_pressed)
        self._broadcaster.jogwheel_rotated_right.connect(self.jg_right)
        self._broadcaster.jogwheel_rotated_left.connect(self.jg_left)
        self._broadcaster.desk_media_scrub_pressed.connect(self.scrub_pressed)
        self._broadcaster.desk_media_scrub_released.connect(self.scrub_released)
        self._broadcaster_signals_connected = True
        self._bankset = BankSet(gui_controlled=True)
        self._bankset.description = f"Live Editor BS for {self._filter_instance.filter_id if self._filter_instance is not None else ""}"
        self._bankset.link()
        self._bankset.activate()

        self._zoom_label: QLabel | None = QLabel()

        self._timeline_container.bankset = self._bankset
        for c in self._timeline_container.cue.channels:
            self._link_column_to_channel(c[0], c[1], True)
        self._bankset.update()
        BankSet.push_messages_now()
        if self._filter_instance:
            self._filter_instance.in_preview_mode = True
            transmit_to_fish(self._filter_instance.scene.board_configuration, False)
            # TODO switch to scene of filter

    def _unlink_broadcaster(self):
        self._broadcaster.desk_media_rec_pressed.disconnect(self._rec_pressed)
        self._broadcaster.jogwheel_rotated_right.disconnect(self.jg_right)
        self._broadcaster.jogwheel_rotated_left.disconnect(self.jg_left)
        self._broadcaster.desk_media_scrub_pressed.disconnect(self.scrub_pressed)
        self._broadcaster.desk_media_scrub_released.disconnect(self.scrub_released)
        self._broadcaster_signals_connected = False

    @abstractmethod
    def _rec_pressed(self):
        raise NotImplementedError()

    def jg_right(self):
        if self._jw_zoom_mode:
            self._timeline_container.increase_zoom(1.25)
            self._set_zoom_label_text()
        else:
            self._timeline_container.move_cursor_right()

    def jg_left(self):
        if self._jw_zoom_mode:
            self._timeline_container.decrease_zoom(1.25)
            self._set_zoom_label_text()
        else:
            self._timeline_container.move_cursor_left()

    def scrub_pressed(self):
        self._jw_zoom_mode = True

    def scrub_released(self):
        self._jw_zoom_mode = False

    def _set_zoom_label_text(self):
        self._zoom_label.setText(self._timeline_container.format_zoom())
