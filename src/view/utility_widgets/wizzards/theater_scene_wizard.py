from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QWizard, QLabel, QFormLayout, QLineEdit, QCheckBox, \
    QHBoxLayout, QListWidget, QPushButton, QGridLayout, QButtonGroup, QRadioButton, QScrollArea

from model import BoardConfiguration
from model.ofl.fixture import ColorSupport
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem
from view.utility_widgets.universe_tree_browser_widget import UniverseTreeBrowserWidget
from view.utility_widgets.wizzards._composable_wizard_page import ComposableWizardPage


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
                                       "fixtures fill be ignored. The selection of individual properties of the "
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
        layout.addWidget(self._feature_grouping_list)
        self._channel_selection_page.setLayout(layout)

        self._channel_setup_page = ComposableWizardPage(page_activation_function=self._initialize_channel_setup_page)
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

        self._preview_page = ComposableWizardPage(page_activation_function=self._initialize_preview_page)
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
        self._fixture_feature_list.clear()
        selected_fixtures = self._fixture_selection_browser.get_selected_fixtures()
        for f in selected_fixtures:
            fcs = f.color_support()
            for supported_mode, name in [
                (ColorSupport.HAS_RGB_SUPPORT, "Color"),
                (ColorSupport.HAS_AMBER_SEGMENT, "Amber"),
                (ColorSupport.HAS_WHITE_SEGMENT, "White"),
                (ColorSupport.HAS_UV_SEGMENT, "UV")
            ]:
                if fcs & supported_mode > 0:
                    item = AnnotatedListWidgetItem(self._fixture_feature_list)
                    item.annotated_data = (f, supported_mode)
                    item.setText("({}:{}) {}: {}".format(f.parent_universe, f.channels[0].address, f.name, name))
                    self._fixture_feature_list.addItem(item)
            remaining_channels = []
            already_added_channels = (f.uv_segments + f.white_segments + f.green_segments + f.blue_segments +
                                      f.red_segments + f.amber_segments)
            for fc in f.channels:
                if fc not in already_added_channels:
                    remaining_channels.append(fc)
            for c in remaining_channels:
                item = AnnotatedListWidgetItem(self._fixture_feature_list)
                item.annotated_data = (f, None)
                item.setText("({}:{}) {}: [undef] {}/".format(f.parent_universe, f.channels[0].address, f.name,
                                                              c.address, c.fixture_channel))
                self._fixture_feature_list.addItem(item)

    def add_group_to_feature_group_list_pressed(self):
        pass  # TODO add group to self.channels and self._feature_grouping_list

    def add_feature_to_feature_group_pressed(self):
        pass  # TODO add feature from _fixture_feature_list to group in self.channels and update item in
              #  self._feature_grouping_list

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
        for c in self._channels:
            i += 1
            controlled_by_desk = c.get("desk-controlled") == "true"
            text_edit = QLineEdit(c.get("name") or str(i), page)
            layout.addItem(text_edit, i, 0)
            radio_group = QButtonGroup(page)
            radio_button_cue = QRadioButton("Cue", page)
            radio_button_cue.setChecked(not controlled_by_desk)
            radio_button_desk = QRadioButton("Desk", page)
            radio_button_desk.setChecked(controlled_by_desk)
            radio_button_desk.setEnabled(is_creation_of_banksets_enabled)
            radio_group.addButton(radio_button_cue)
            radio_group.addButton(radio_button_desk)
            layout.addItem(radio_group, i, 1)
            self._channel_setup_widgets.append((text_edit, radio_group, radio_button_cue, radio_button_desk))

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
        # TODO populate self.channels
        self._populate_channel_setup_page()

    def _initialize_preview_page(self, page: ComposableWizardPage):
        pass  # TODO fill label with data that is about to be inserted inside the scene
