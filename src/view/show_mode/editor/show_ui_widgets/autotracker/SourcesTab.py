import cv2
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QLayout,
    QPushButton,
    QFileDialog,
    QDialog,
    QComboBox,
)

from view.show_mode.editor.show_ui_widgets.autotracker.GuiTab import GuiTab
from controller.autotrack.ImageOptimizer.BasicOptimizer import CropOptimizer
from controller.autotrack.ImageOptimizer.ImagePipeline import ImagePipeline
from controller.autotrack.Helpers.ImageHelper import cv2qim
from controller.autotrack.Sources.CameraLoader import CameraLoader
from controller.autotrack.Sources.FileLoader import FileLoader
from controller.autotrack.Helpers.InstanceManager import InstanceManager
from controller.autotrack.Sources.FrameManager import FrameManager


class SourcesTab(GuiTab):
    """
    The `SourcesTab` class represents a tab for managing video sources.

    Attributes:
        name (str): The name of the tab.
        instance (InstanceManager): An instance manager for managing application instances and settings.
        video_running (bool): Indicates whether video playback is active.

    Methods:
        - `__init__(name, instance)`: Initialize a SourcesTab object with a name and an instance manager.
        - `video_update()`: Update the video content within the tab.
        - `show_file_dialog()`: Show a file dialog to select a video file.
        - `tab_deactivated()`: Called when the tab is deactivated.
    """

    def tab_activated(self):
        """
        Called when the tab is activated.
        """
        super().tab_activated()

    def __init__(self, name, instance: InstanceManager):
        """
        Initialize a SourcesTab object.

        Args:
            name (str): The name of the tab.
            instance (InstanceManager): An instance manager for managing application instances and settings.
        """
        super().__init__(name, instance)
        self.video_running = False

        self.image_label = QLabel()

        self.layout = QVBoxLayout()
        self.layout.setSizeConstraint(QLayout.SetMinimumSize)

        self.btn_video = QPushButton("Load Video File")
        self.btn_video.clicked.connect(self.show_file_dialog)

        self.btn_webcam = QPushButton("Open default Webcam")
        self.btn_webcam.clicked.connect(self.load_webcam)

        self.layout.addWidget(self.btn_webcam)
        self.layout.addWidget(self.btn_video)
        self.layout.addWidget(self.image_label)
        self.setLayout(self.layout)

        # Setup Frame Manager
        self.frame_thread = FrameManager()
        self.frame_thread.frame_captured.connect(self.update_frame)
        self.frame_thread.start()

    def load_webcam(self):
        print("click")

        dlg = WebcamSelector()
        dlg.exec_()
        selected_index = dlg.comboBox.currentIndex()
        print(selected_index)
        loader = CameraLoader(selected_index)
        self.instance.set_loader(loader)
        self.frame_thread.change_loader(loader)
        self.video_running = True
        self.video_update()

    def video_update(self):
        frame = self.instance.settings.next_frame
        if frame is not None and self.video_running and self.active:
            frame = self.instance.get_preview_pipeline().optimize(frame)
            crop = self.instance.settings.crop
            h, w, *_ = frame.shape

            frame = CropOptimizer(
                "crop", (crop[2], h - crop[3], crop[0], w - crop[1])
            ).process(frame)
            self.image_label.setPixmap(cv2qim(frame))

    def video_update_old(self):
        """
        Update the video content within the tab.
        """
        loader = self.instance.get_loader()
        if loader is not None and self.video_running and self.active:
            frame = loader.get_last(-1)
            frame = self.instance.get_preview_pipeline().optimize(frame)
            crop = self.instance.settings.crop
            h, w, *_ = frame.shape

            frame = CropOptimizer(
                "crop", (crop[2], h - crop[3], crop[0], w - crop[1])
            ).process(frame)
            self.image_label.setPixmap(cv2qim(frame))

    def show_file_dialog(self):
        """
        Show a file dialog to select a video file.
        """
        options = QFileDialog.Options()

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "MP4 (*.mp4);;All Files (*)",
            options=options,
        )
        if file_name:
            print(file_name)
            loader = FileLoader(True)
            loader.load_file(path=file_name)
            self.instance.set_loader(loader)
            self.frame_thread.change_loader(loader)
            self.video_running = True
            self.video_update()

    def tab_deactivated(self):
        """
        Called when the tab is deactivated.
        """
        super().tab_deactivated()

    def update_frame(self, frame):
        self.instance.settings.next_frame = frame


class WebcamSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Webcam Selector")
        self.setMinimumWidth(300)

        self.label = QLabel("Select a webcam:")
        self.comboBox = QComboBox(self)
        self.startButton = QPushButton("Start", self)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.comboBox)
        layout.addWidget(self.startButton)
        self.startButton.clicked.connect(self.accept)
        self.setLayout(layout)

        self.startButton.clicked.connect(self.start_webcam)

        self.populate_webcams()

    def populate_webcams(self):
        # Use OpenCV to enumerate available webcams
        # num_webcams = len([i for i in range(10) if cv2.VideoCapture(i).isOpened()])
        num_webcams = 5
        for i in range(num_webcams):
            self.comboBox.addItem(f"Webcam {i}")

    def start_webcam(self):
        selected_index = self.comboBox.currentIndex()
        if selected_index >= 0:
            print(f"selected webcam {selected_index}")
