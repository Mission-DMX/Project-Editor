from PySide6.QtWidgets import QWidget, QVBoxLayout, QWizard, QWizardPage, QLabel

from model import BoardConfiguration


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
        self._meta_page = QWizardPage()  # TODO Form layout with scene name, if global illumination should be honored,
        # should there be bank set inputs
        self._fixture_page = QWizardPage()  # TODO select the fixtures that should be added
        self._channel_selection_page = QWizardPage()  # TODO page where the user can select the fixture features that
        # should be used, as well as grouping them
        self._channel_setup_page = QWizardPage()  # TODO page where the user can rename each channel and decide if it
        # should be controlled by cue or desk column
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
