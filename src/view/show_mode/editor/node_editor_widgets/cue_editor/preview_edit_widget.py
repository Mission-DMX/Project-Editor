from abc import ABC, abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget

from controller.file.transmitting_to_fish import transmit_to_fish
from model import Broadcaster, DataType, Filter
from model.control_desk import BankSet, ColorDeskColumn, DeskColumn, RawDeskColumn
from model.virtual_filters.cue_vfilter import PreviewFilter
from view.show_mode.editor.node_editor_widgets.cue_editor.timeline_editor import TimelineContainer
from view.show_mode.editor.node_editor_widgets.node_editor_widget import NodeEditorFilterConfigWidget

logger = getLogger(__file__)

if TYPE_CHECKING:
    from view.show_mode.editor.nodes import FilterNode


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
        self.bs_to_channel_mapping: dict[str, DeskColumn] = {}

        self._timeline_container = TimelineContainer(None)
        self._timeline_container.setEnabled(False)
        self._timeline_container.transition_type = "lin"
        self._jw_zoom_mode = False
        self._gui_rec_action = QAction("Record keyframe")
        self._gui_rec_action.setStatusTip("Insert a Keyframe at the current cursor position")
        self._gui_rec_action.setIcon(QIcon.fromTheme("media-record"))
        self._gui_rec_action.setEnabled(False)
        self._gui_rec_action.triggered.connect(self._rec_pressed)

        self._zoom_label: QLabel | None = QLabel()
        self.zoom_panel = QWidget()
        zoom_panel_layout = QHBoxLayout()
        self.zoom_panel.setLayout(zoom_panel_layout)
        zoom_panel_layout.addWidget(self._zoom_label)
        increase_zoom_button = QPushButton("+", self.zoom_panel)
        increase_zoom_button.pressed.connect(self.increase_zoom)
        zoom_panel_layout.addWidget(increase_zoom_button)
        decrease_zoom_button = QPushButton("-", self.zoom_panel)
        decrease_zoom_button.pressed.connect(self.decrease_zoom)
        zoom_panel_layout.addWidget(decrease_zoom_button)
        self.transition_type_select_widget = QComboBox()
        self.transition_type_select_widget.addItems(["lin", "edg", "sig", "e_i", "e_o"])
        self.transition_type_select_widget.currentTextChanged.connect(self._transition_type_changed)

        self._filter_instance: PreviewFilter | None = f if isinstance(f, PreviewFilter) else None
        if self._filter_instance:
            self._filter_instance.associated_editor_widget = self
        else:
            logger.error("Preview editor widget received invalid filter: %s.", f)
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

    def connect_to_broadcaster(self):
        self._broadcaster.desk_media_rec_pressed.connect(self._rec_pressed)
        self._broadcaster.jogwheel_rotated_right.connect(self.jg_right)
        self._broadcaster.jogwheel_rotated_left.connect(self.jg_left)
        self._broadcaster.desk_media_scrub_pressed.connect(self.scrub_pressed)
        self._broadcaster.desk_media_scrub_released.connect(self.scrub_released)
        self._broadcaster_signals_connected = True

    def _link_bankset(self):
        if not self._broadcaster_signals_connected:
            self.connect_to_broadcaster()
        if self._bankset is not None:
            self._bankset.unlink()
            BankSet.push_messages_now()
        self._bankset = BankSet(gui_controlled=True)
        self._bankset.description = f"Live Editor BS for {self._filter_instance.filter_id if self._filter_instance is not None else ""}"
        self._bankset.link()
        self._bankset.activate()

        self._timeline_container.bankset = self._bankset
        for c in self._get_model_channels():
            self.link_column_to_channel(c[0], c[1], True)
        self._bankset.update()
        BankSet.push_messages_now()
        if self._filter_instance:
            self._filter_instance.in_preview_mode = True
            transmit_to_fish(self._filter_instance.scene.board_configuration, False)
            # TODO switch to scene of filter if different scene

    def disconnect_from_broadcaster(self):
        self._broadcaster.desk_media_rec_pressed.disconnect(self._rec_pressed)
        self._broadcaster.jogwheel_rotated_right.disconnect(self.jg_right)
        self._broadcaster.jogwheel_rotated_left.disconnect(self.jg_left)
        self._broadcaster.desk_media_scrub_pressed.disconnect(self.scrub_pressed)
        self._broadcaster.desk_media_scrub_released.disconnect(self.scrub_released)
        self._broadcaster_signals_connected = False

    @abstractmethod
    def _rec_pressed(self):
        raise NotImplementedError()

    def _get_model_channels(self) -> list[tuple[str, DataType]]:
        return self._timeline_container.cue.channels

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

    def increase_zoom(self):
        self._timeline_container.increase_zoom()
        self._set_zoom_label_text()

    def decrease_zoom(self):
        self._timeline_container.decrease_zoom()
        self._set_zoom_label_text()

    def _transition_type_changed(self, text):
        self._timeline_container.transition_type = text

    def link_column_to_channel(self, channel_name, channel_type, is_part_of_mass_update):
        if not self._bankset:
            return
        if channel_type == DataType.DT_COLOR:
            c = ColorDeskColumn()
        else:
            c = RawDeskColumn()
        c.display_name = channel_name
        self._bankset.add_column_to_next_bank(c)
        self.bs_to_channel_mapping[channel_name] = c
        if not is_part_of_mass_update:
            self._bankset.update()

    def _update_terminals(self, filter_node: "FilterNode"):
        if self._filter_instance is None:
            return
        required_channels: set[tuple[str, DataType]] = set()
        existing_channels: set[tuple[str, DataType]] = set()
        for c in self.channels:
            required_channels.add((c.name, c.data_type))
        for t in filter_node.outputs().keys():
            existing_channels.add((t, self._filter_instance.out_data_types.get(t)))
        for name, _ in existing_channels - required_channels:
            self._filter_instance.out_data_types.pop(name)
            filter_node.removeTerminal(name)
        for name, dtype in required_channels - existing_channels:
            filter_node.addOutput(name=name)
            self._filter_instance.out_data_types[name] = dtype

    def parent_closed(self, filter_node: "FilterNode"):
        self._timeline_container.clear_display()
        self._update_terminals(filter_node)
        if self._bankset:
            self._bankset.unlink()
            BankSet.push_messages_now()
        show_reset_required = False
        if self._broadcaster and self._broadcaster_signals_connected:
            self.disconnect_from_broadcaster()
            show_reset_required = True
        if self._filter_instance:
            self._filter_instance.in_preview_mode = False
            if show_reset_required:
                transmit_to_fish(self._filter_instance.scene.board_configuration, False)
                # TODO switch to scene of filter
        super().parent_closed(filter_node)
