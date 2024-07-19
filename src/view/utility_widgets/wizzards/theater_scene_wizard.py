from PySide6.QtWidgets import QWidget, QVBoxLayout, QWizard, QWizardPage, QLabel, QFormLayout, QLineEdit, QCheckBox, \
    QHBoxLayout, QListWidget, QPushButton

from model import BoardConfiguration
from view.utility_widgets.universe_tree_browser_widget import UniverseTreeBrowserWidget


class TheaterSceneWizard(QWizard):
    def __init__(self, parent: QWidget, show: BoardConfiguration):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(600, 300)
        self.setWindowTitle("Theatrical Scene Wizard")
        self._introduction_page = QWizardPage()
        self._introduction_page.setTitle("Introduction")
        self._introduction_label = QLabel("This wizard guides you through the automatic creation of a scene used for "
                                          "theater productions. You can select a set of fixtures that should be used "
                                          "and it will automatically add them as well as inter connect it with a Cue "
                                          "filter. Last but not least, you may choose a set of properties that you "
                                          "would like to control within that scene and this wizard will automatically "
                                          "create the required channels and connections for you.<br />Click next to "
                                          "continue.")
        self._introduction_label.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addWidget(self._introduction_label)
        self._introduction_page.setLayout(layout)

        self._meta_page = QWizardPage()
        layout = QFormLayout()
        self._scene_name_tb = QLineEdit(self._meta_page)
        self._scene_name_tb.setToolTip("Enter the human readable name of this scene. The ID will be set automatically.")
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

        self._fixture_page = QWizardPage()
        layout = QVBoxLayout()
        self._fixture_selection_browser = UniverseTreeBrowserWidget(show, True)
        layout.addWidget(self._fixture_selection_browser)
        self._fixture_page.setLayout(layout)

        self._channel_selection_page = QWizardPage()
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

        self._channel_setup_page = QWizardPage()
        # TODO page where the user can rename each channel and decide if it
        #  should be controlled by cue or desk column
        self._cues_page = QWizardPage()  # TODO page where the user can add and name cues and set up their properties
        self._preview_page = QWizardPage()  # TODO final preview and confirmation page
        self.addPage(self._introduction_page)
        self.addPage(self._meta_page)
        self.addPage(self._fixture_page)
        self.addPage(self._channel_selection_page)
        self.addPage(self._channel_setup_page)
        self.addPage(self._cues_page)
        self.addPage(self._preview_page)
        self._show = show

    def add_group_to_feature_group_list_pressed(self):
        pass  # TODO

    def add_feature_to_feature_group_pressed(self):
        pass  # TODO
