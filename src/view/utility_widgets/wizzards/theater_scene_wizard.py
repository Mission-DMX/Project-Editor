# coding=utf-8
import logging
import os.path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QWizard,
)

from controller.utils.process_notifications import get_process_notifier
from model import BoardConfiguration, Scene
from model.channel import Channel
from model.filter import DataType, Filter, FilterTypeEnumeration
from model.ofl.fixture import ColorSupport, UsedFixture
from model.patching.fixture_channel import FixtureChannelType
from model.virtual_filters.vfilter_factory import construct_virtual_filter_instance
from utility import resource_path
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue import Cue
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue_filter_model import CueFilterModel
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem
from view.show_mode.editor.show_browser.fixture_to_filter import place_fixture_filters_in_scene
from view.utility_widgets.button_container import ButtonContainer
from view.utility_widgets.universe_tree_browser_widget import UniverseTreeBrowserWidget
from view.utility_widgets.wizzards._composable_wizard_page import ComposableWizardPage

_folder_empty_icon = QIcon(resource_path(os.path.join("resources", "icons", "folder.svg")))
_folder_full_icon = QIcon(resource_path(os.path.join("resources", "icons", "folder-full.svg")))
logger = logging.getLogger(__file__)


def _d_assign(d, v, k):
    d[v] = k

#TODO komplett überarbeiten
class TheaterSceneWizard(QWizard):
    def __init__(self, parent: QWidget, show: BoardConfiguration):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(600, 300)
        self.setWindowTitle("Theatrical Scene Wizard")
        self._introduction_page = ComposableWizardPage()
        self._introduction_page.setTitle("Introduction")
        self._introduction_label = QLabel("This wizard guides you through the automatic creation of a scene used for "
                                          "theater productions. You can select a set of fixtures that should be used "
                                          "and it will automatically add them as well as inter connect it with a Cue "
                                          "filter. Last but not least, you may choose a set of properties that you "
                                          "would like to control within that scene and this wizard will automatically "
                                          "create the required channels and connections for you.<br />Click next to "
                                          "continue.")
        self._introduction_page.setFinalPage(False)
        self._introduction_label.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addWidget(self._introduction_label)
        self._introduction_page.setLayout(layout)

        self._meta_page = ComposableWizardPage()
        self._meta_page.setTitle("General Setup")
        self._meta_page.setSubTitle("Enter the general properties of the new scene you want to create.")
        self._meta_page.setFinalPage(False)
        layout = QFormLayout()
        self._scene_name_tb = QLineEdit(self._meta_page)
        self._scene_name_tb.setToolTip("Enter the human readable name of this scene. The ID will be set automatically.")
        self._meta_page.registerField("name*", self._scene_name_tb)
        layout.addRow("Scene name:", self._scene_name_tb)
        self._honor_global_illumination_cb = QCheckBox("Honor global illumination", self._meta_page)
        self._honor_global_illumination_cb.setChecked(True)
        layout.addRow("", self._honor_global_illumination_cb)
        self._create_ui_widgets_cb = QCheckBox("Create a cue control UI widget", self._meta_page)
        self._create_ui_widgets_cb.setChecked(True)
        layout.addRow("", self._create_ui_widgets_cb)
        self._create_bank_set_controls_cb = QCheckBox("Create Bank Set controls", self._meta_page)
        layout.addRow("", self._create_bank_set_controls_cb)
        self._meta_page.setLayout(layout)

        self._fixture_page = ComposableWizardPage()
        self._fixture_page.setTitle("Fixture Selection")
        self._fixture_page.setSubTitle("Please select the fixtures you'd like to use in your new scene. All other "
                                       "fixtures will be ignored. The selection of individual properties of the "
                                       "fixtures is done at a later stage.")
        self._fixture_page.setFinalPage(False)
        layout = QVBoxLayout()
        self._fixture_selection_browser = UniverseTreeBrowserWidget(show, True)
        layout.addWidget(self._fixture_selection_browser)
        self._fixture_page.setLayout(layout)

        self._channel_selection_page = ComposableWizardPage(page_activation_function=self._init_channel_selection_page)
        self._channel_selection_page.setTitle("Channel Selection")
        self._channel_selection_page.setSubTitle("Please select which features of the selected fixtures you'd like to "
                                                 "use and assign them to property channels.")
        self._channel_selection_page.setFinalPage(False)
        layout = QHBoxLayout()
        self._fixture_feature_list = QListWidget(self._channel_selection_page)
        self._fixture_feature_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._fixture_feature_list)
        sec_layout = QVBoxLayout()
        sec_layout.addStretch()
        self._channel_selection_page_new_group_button = QPushButton("Add Group", self._channel_selection_page)
        self._channel_selection_page_new_group_button.setToolTip("Add a new group.")
        self._channel_selection_page_new_group_button.clicked.connect(self.add_group_to_feature_group_list_pressed)
        sec_layout.addWidget(self._channel_selection_page_new_group_button)
        self._channel_selection_page_add_feature_to_group_button = QPushButton(
            "Add feature", self._channel_selection_page
        )
        self._channel_selection_page_add_feature_to_group_button.setToolTip(
            "Add the selected feature to the selected group."
        )
        self._channel_selection_page_add_feature_to_group_button.clicked.connect(
            self.add_feature_to_feature_group_pressed
        )
        sec_layout.addWidget(self._channel_selection_page_add_feature_to_group_button)
        sec_layout.addStretch()
        layout.addLayout(sec_layout)
        self._feature_grouping_list = QListWidget(self._channel_selection_page)
        self._feature_grouping_list.itemChanged.connect(self._feature_grouping_item_changed)
        self._feature_grouping_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._feature_grouping_list)
        self._channel_selection_page.setLayout(layout)

        self._channel_setup_page = ComposableWizardPage(page_activation_function=self._initialize_channel_setup_page,
                                                        check_completeness_function=self._finish_channel_setup_page)
        self._channel_setup_page.setTitle("Channel Setup")
        self._channel_setup_page.setSubTitle("Please assign the names of previous channels and select their "
                                             "control method.")
        self._channel_setup_page.setFinalPage(False)
        self._channel_setup_widgets: list[tuple[QLineEdit, QButtonGroup, QRadioButton, QRadioButton]] = []
        layout = QHBoxLayout()
        self._channel_setup_widgets_scroll_area = QScrollArea(self._channel_setup_page)
        layout.addWidget(self._channel_setup_widgets_scroll_area)
        self._channel_setup_page.setLayout(layout)
        layout = QGridLayout()
        self._channel_setup_widgets_scroll_area.setLayout(layout)

        self._cues_page = ComposableWizardPage()
        self._cues_page.setTitle("Cue setup")
        self._cues_page.setSubTitle("Please create the cues you'd like to use. Edit names by double clicking them.")
        self._cues_page.setFinalPage(True)
        layout = QVBoxLayout()
        sec_layout = QHBoxLayout()
        self._cues_page_add_cue_button = QPushButton("Add Cue", self._cues_page)
        self._cues_page_add_cue_button.setToolTip("Define a new cue that should be added.")
        self._cues_page_add_cue_button.clicked.connect(self._add_cue_button_pressed)
        sec_layout.addWidget(self._cues_page_add_cue_button)
        sec_layout.addStretch()
        self._cues_page_rm_cue_button = QPushButton("Remove Cue", self._cues_page)
        self._cues_page_rm_cue_button.setToolTip("Remove the selected cue.")
        self._cues_page_rm_cue_button.clicked.connect(self._remove_cue_button_pressed)
        sec_layout.addWidget(self._cues_page_rm_cue_button)
        layout.addLayout(sec_layout)
        self._cues_page_cue_list_widget = QListWidget(self._cues_page)
        layout.addWidget(self._cues_page_cue_list_widget)
        self._cues_page.setLayout(layout)

        self._preview_page = ComposableWizardPage(page_activation_function=self._initialize_preview_page,
                                                  check_completeness_function=self._commit_changes)
        self._preview_page.setTitle("Preview")
        self._preview_page.setSubTitle("Please review and confirm the changes that are about to be made.")
        self._preview_page.setFinalPage(True)
        layout = QVBoxLayout()
        self._preview_text_area = QLabel(self._preview_page)
        layout.addWidget(self._preview_text_area)

        self.addPage(self._introduction_page)
        self.addPage(self._meta_page)
        self.addPage(self._fixture_page)
        self.addPage(self._channel_selection_page)
        self.addPage(self._channel_setup_page)
        self.addPage(self._cues_page)
        self.addPage(self._preview_page)
        self._show = show
        self._channels: list[dict[str, str]] = []

    def _init_channel_selection_page(self, page: ComposableWizardPage):
        self._feature_grouping_list.clear()
        self._fixture_feature_list.clear()
        selected_fixtures = self._fixture_selection_browser.get_selected_fixtures()
        for f in selected_fixtures:
            # Map color channels
            fcs = f.color_support
            for supported_mode, name in [
                (ColorSupport.HAS_RGB_SUPPORT, "Color"),
                (ColorSupport.HAS_AMBER_SEGMENT, "Amber"),
                (ColorSupport.HAS_WHITE_SEGMENT, "White"),
                (ColorSupport.HAS_UV_SEGMENT, "UV")
            ]:
                if fcs & supported_mode > 0:
                    item = AnnotatedListWidgetItem(self._fixture_feature_list)
                    item.annotated_data = (f, supported_mode)
                    item.setText(f"({f.parent_universe}:{f.start_index}) {f.name}: {name}")
                    self._fixture_feature_list.addItem(item)

            # Map position Channels
            for type_ in [("Pan", f.get_segment_in_universe_by_type(
                FixtureChannelType.PAN)), ("Tilt", f.get_segment_in_universe_by_type(
                FixtureChannelType.TILT)),  # TODO public and not np
                          ("Animation Speed", f.get_segment_in_universe_by_type(
                FixtureChannelType.SPEED))]:
                mode = type_[0]
                for _ in type_[1]:
                    item = AnnotatedListWidgetItem(self._fixture_feature_list)
                    item.annotated_data = (f, mode)
                    item.setText(f"({f.parent_universe}:{f.start_index}) {f.name}: {mode}")
                    self._fixture_feature_list.addItem(item)

            remaining_channels: list[int] = []

            already_added_channels = (f.get_segment_in_universe_by_type(
                FixtureChannelType.UV) + f.get_segment_in_universe_by_type(
                FixtureChannelType.WHITE) + f.get_segment_in_universe_by_type(
                FixtureChannelType.GREEN) + f.get_segment_in_universe_by_type(
                FixtureChannelType.BLUE) +                                      f.get_segment_in_universe_by_type(
                                          FixtureChannelType.RED) + f.get_segment_in_universe_by_type(
                FixtureChannelType.AMBER) +f.get_segment_in_universe_by_type(
                FixtureChannelType.PAN) + f.get_segment_in_universe_by_type(
                FixtureChannelType.TILT) +
                                      f.get_segment_in_universe_by_type(
                                          FixtureChannelType.SPEED))  # TODO public and not np
            for fc in f._fixture_channels:  # TODO public and not np
                if fc not in already_added_channels:
                    remaining_channels.append(fc)

            for c in remaining_channels:
                item = AnnotatedListWidgetItem(self._fixture_feature_list)
                # item.annotated_data = (f, c) #TODO für was
                item.setText(
                    f"({f.parent_universe}:{f.start_index}) {f.name}: [undef] {c} {f.get_fixture_channel(c).name}/")
                self._fixture_feature_list.addItem(item)

    def add_group_to_feature_group_list_pressed(self):
        item = AnnotatedListWidgetItem(self._feature_grouping_list)
        item.setText("New Group")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        item.setIcon(_folder_empty_icon)
        d = {"name": "New Group", "fixtures": []}
        item.annotated_data = d
        self._channels.append(d)
        self._feature_grouping_list.addItem(item)

    def _feature_grouping_item_changed(self, item):
        if not isinstance(item, AnnotatedListWidgetItem):
            return
        if item.annotated_data is None:
            logger.error("Expected item to contain annotated data")
            return
        item.annotated_data["name"] = item.text()

    def add_feature_to_feature_group_pressed(self):
        selected_group = self._feature_grouping_list.selectedItems()
        if len(selected_group) > 0:
            selected_group = selected_group[0]
        else:
            selected_group = None
        selected_feature = self._fixture_feature_list.selectedItems()
        if len(selected_feature) > 0:
            selected_feature = selected_feature[0]
        else:
            return
        if (not isinstance(selected_feature, AnnotatedListWidgetItem) or
                (not isinstance(selected_group, AnnotatedListWidgetItem) and selected_group is not None)):
            raise ValueError("Expected Annotated List Widget Item")
        if selected_group:
            first_item_in_group = selected_group.toolTip() == ""
            selected_group.setToolTip((", " if not first_item_in_group else "") + selected_group.toolTip() +
                                      selected_feature.text())
            if first_item_in_group:
                selected_group.setIcon(_folder_full_icon)
            selected_group.annotated_data["fixtures"].append(selected_feature.annotated_data)
            selected_group.setToolTip("Content: " + ",".join(
                [f"{i[0].parent_universe}/{str(i[0].start_index)}: {i[0].color_support}" for i in
                 selected_group.annotated_data["fixtures"]]))
        else:
            new_group_item = AnnotatedListWidgetItem(self._feature_grouping_list)
            new_group_item.setText(selected_feature.text())
            new_group_item.setToolTip(selected_feature.text())
            new_group_item.annotated_data = {
                "name": selected_feature.text(),
                "fixtures": [selected_feature.annotated_data]
            }
            self._feature_grouping_list.addItem(new_group_item)
            self._channels.append(new_group_item.annotated_data)
        self._fixture_feature_list.takeItem(self._fixture_feature_list.row(selected_feature))

    def _populate_channel_setup_page(self):
        page = self._channel_setup_widgets_scroll_area
        layout = page.layout()
        for edit, button_group, b1, b2 in self._channel_setup_widgets:
            layout.removeWidget(edit)
            layout.removeWidget(b1)
            layout.removeWidget(b2)
            layout.removeWidget(button_group)
        self._channel_setup_widgets.clear()
        is_creation_of_banksets_enabled = self._create_bank_set_controls_cb.isChecked()
        i = 0
        self._guess_cue_channel_data_types()
        for c in self._channels:
            i += 1
            controlled_by_desk = c.get("desk-controlled") == "true"
            text_edit = QLineEdit(c.get("name") or str(i), page)
            text_edit.textChanged.connect(lambda text, d=c: _d_assign(d, "name", text))
            layout.addWidget(text_edit, i, 0)
            button_container = ButtonContainer(page)
            radio_button_cue = QRadioButton("Cue", page)
            radio_button_cue.setChecked(not controlled_by_desk)
            radio_button_cue.clicked.connect(lambda checked=False, d=c: _d_assign(d, "desk-controlled", "true"))
            radio_button_desk = QRadioButton("Desk", page)
            radio_button_desk.setChecked(controlled_by_desk)
            radio_button_desk.setEnabled(is_creation_of_banksets_enabled)
            radio_button_desk.clicked.connect(lambda checked=False, d=c: _d_assign(d, "desk-controlled", "false"))
            button_container.add_button(radio_button_cue)
            button_container.add_button(radio_button_desk)
            layout.addWidget(button_container, i, 1)
            data_type_combo_box = QComboBox(page)
            data_type_combo_box.addItems([dt.format_for_filters() for dt in [
                DataType.DT_COLOR, DataType.DT_8_BIT, DataType.DT_16_BIT, DataType.DT_DOUBLE
            ]])
            item_index = 0
            match c.get("data-type"):
                case DataType.DT_DOUBLE:
                    item_index = 3
                case DataType.DT_16_BIT:
                    item_index = 2
                case DataType.DT_8_BIT:
                    item_index = 1
                case DataType.DT_COLOR:
                    item_index = 0
            data_type_combo_box.setCurrentIndex(item_index)
            data_type_combo_box.currentTextChanged.connect(
                lambda selected_mode, d=c: _d_assign(d, "data-type", DataType.from_filter_str(selected_mode)))
            layout.addWidget(data_type_combo_box, i, 2)
            self._channel_setup_widgets.append((text_edit, button_container, radio_button_cue, radio_button_desk))

    def _finish_channel_setup_page(self, page: ComposableWizardPage):
        return True

    def _add_cue_button_pressed(self):
        item = AnnotatedListWidgetItem(self._cues_page_cue_list_widget)
        item.setText("New Cue")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self._cues_page_cue_list_widget.addItem(item)

    def _remove_cue_button_pressed(self):
        sitems = self._cues_page_cue_list_widget.selectedItems()
        for item in sitems:
            self._cues_page_cue_list_widget.takeItem(self._cues_page_cue_list_widget.row(item))

    def _initialize_channel_setup_page(self, page: ComposableWizardPage):
        self._populate_channel_setup_page()

    def _initialize_preview_page(self, page: ComposableWizardPage):
        text = "Channels:<br /><ul>"
        for c in self._channels:
            text += ("<li>" + ("[DESK]" if c.get('desk-controlled') == "true" else "[CUE]") + c.get("name") +
                     ":" + ", ".join([f[0].name for f in c.get("fixtures")]) + "</li>")
        text += "</ul><br>Cues:<br /><ol>"
        for item_c in range(self._cues_page_cue_list_widget.count()):
            item = self._cues_page_cue_list_widget.item(item_c)
            text += '<li>' + item.text() + "</li>"
        text += "</ol>"
        self._preview_text_area.setText(text)

    def _guess_cue_channel_data_types(self):
        for c in self._channels:
            if c.get("data-type") is not None:
                continue
            selected_data_type = DataType.DT_8_BIT
            color_found = False
            position_found = False
            for f in c.get("fixtures"):
                if isinstance(f[1], DataType):
                    if f[1] & ColorSupport.HAS_RGB_SUPPORT > 0:
                        color_found = True
                    if f[1] & ColorSupport.HAS_WHITE_SEGMENT > 0:
                        illumination_found = True
                if isinstance(f[1], str):
                    if f[1] == "Pan" or f[1] == "Tilt":
                        position_found = True

            if color_found and not position_found:
                selected_data_type = DataType.DT_COLOR
            elif position_found:
                selected_data_type = DataType.DT_16_BIT
            # TODO the above only gives us the fixtures that should be linked to this channel as well as its name.
            #  We need to find a way to deduce the data type.
            c["data-type"] = selected_data_type

    def _commit_changes(self, page: ComposableWizardPage):
        pn = get_process_notifier("Create Scene", 6)
        self._guess_cue_channel_data_types()  # This will skip every entry except for the new ones
        # TODO introduce wizard page where the user can manipulate the guessed channel mappings
        pn.current_step_number += 1
        scene = Scene(len(self._show.scenes), self._scene_name_tb.text(), self._show)
        pn.current_step_number += 1
        cue_link_map = self._generate_cue_filter(scene)
        pn.current_step_number += 1
        bankset_link_map = self._generate_bank_set(scene)
        pn.current_step_number += 1
        output_map = self._generate_output_filters(scene)
        pn.current_step_number += 1
        self._link_output_filters(bankset_link_map, cue_link_map, output_map, scene)
        pn.current_step_number += 1
        self._show.broadcaster.scene_created.emit(scene)
        pn.close()
        return True

    def _link_output_filters(self, bankset_link_map, cue_link_map: dict[str, str], output_map, scene):
        for c in self._channels: # TODO  channels have no fixtures
            for fd in c["fixtures"]:
                fixture = fd[0]
                if not isinstance(fixture, UsedFixture):
                    logger.critical("Entry was supposed to be Fixture")
                for patching_channel in fixture.channels:
                    output_channel_id = output_map.get(patching_channel)
                    if output_channel_id is not None:
                        output_channel_id = str(output_channel_id).split(":")
                    else:
                        continue
                    output_filter_to_connect: str = output_channel_id[0]
                    filter_channel_to_connect: str = output_channel_id[1]
                    selected_source_map = bankset_link_map if c.get('desk-controlled') == "true" else cue_link_map
                    # TODO this makes only sense in case of 8bit channels. We need to deal with color conversion
                    #  filters as well
                    selected_channel = selected_source_map.get(patching_channel)
                    if selected_channel:
                        scene.get_filter_by_id(output_filter_to_connect).channel_links[
                            filter_channel_to_connect] = selected_channel

    def _generate_cue_filter(self, scene: Scene) -> dict[str, str]:
        time_filter = Filter(filter_id="Time_Input", filter_type=FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT,
                             scene=scene, pos=(-10, 0))
        scene.append_filter(time_filter, filter_page_index=0)

        cue_filter = construct_virtual_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_CUES,
            filter_id="SceneCueFilter",
            pos=(0, 0)
        )
        cue_filter.channel_links['time'] = time_filter.filter_id + ":value"
        cue_model = CueFilterModel()
        link_map: dict[str, str] = {}
        for c in self._channels:
            if c.get("desk-controlled") != "true":
                associated_channel = c.get("name").replace(" ", "_").replace(":", "")
                fixture_channels: list[str] = []
                associated_fixtures = c.get("fixtures") or []
                match c.get("data-type"):
                    case DataType.DT_8_BIT:
                        # TODO find fixture channel closest associated with name
                        pass
                    case DataType.DT_16_BIT:
                        # TODO find 16bit to 8 bit filter with closest association
                        for f in associated_fixtures:
                            for p in f[0].position_channels:
                                fixture_channels.append(p)

                    case DataType.DT_DOUBLE | DataType.DT_BOOL:
                        # TODO figure out what to do in this case
                        pass
                    case DataType.DT_COLOR:
                        for f in associated_fixtures:
                            if f[1] == ColorSupport.NO_COLOR_SUPPORT:
                                continue
                            proto = f[0].red_segments + f[0].green_segments + f[0].blue_segments
                            for p in proto:
                                fixture_channels.append(p)

                cue_model.add_channel(associated_channel, DataType.from_filter_str(c["data-type"]))
                for pc in fixture_channels:
                    link_map[pc] = f"{cue_filter.filter_id}:{associated_channel}"
        scene.append_filter(cue_filter, filter_page_index=0)
        for cue_request_index in range(self._cues_page_cue_list_widget.count()):
            c = Cue()
            c.name = self._cues_page_cue_list_widget.item(cue_request_index).text()
            cue_model.append_cue(c)
        cue_filter.filter_configurations.update(cue_model.get_as_configuration())
        return link_map

    def _generate_output_filters(self, scene: Scene) -> dict:
        placed_fixtures: list[UsedFixture] = []
        output_map = {}
        fp = scene.pages[0]
        for c in self._channels:
            for f in c["fixtures"]:
                if f not in placed_fixtures:
                    placed_fixtures.append(f)
                    if not place_fixture_filters_in_scene(f, fp, output_map=output_map):
                        logger.error("Failed to place output filters for fixture %s in scene with id %s.", f,
                                     scene.scene_id
                                     )
        return output_map

    def _generate_bank_set(self, scene: Scene) -> dict[Channel, str]:
        return {}  # TODO
