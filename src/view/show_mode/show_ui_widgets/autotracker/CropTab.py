from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QLayout, QSlider

from controller.autotrack.Helpers.ImageHelper import cv2qim, draw_overlay
from controller.autotrack.Helpers.InstanceManager import InstanceManager
from view.show_mode.show_ui_widgets.autotracker.GuiTab import GuiTab


class CropTab(GuiTab):
    """
    The `CropTab` class represents a tab for configuring cropping settings.

    Attributes:
        name (str): The name of the tab.
        instance (InstanceManager): An instance manager for managing application instances and settings.
        layout (QGridLayout): The layout for the tab.
        image_label (QLabel): A label for displaying an image.
        sliderx1 (QSlider): A slider for adjusting the left crop boundary.
        sliderx2 (QSlider): A slider for adjusting the right crop boundary.
        slidery1 (QSlider): A slider for adjusting the top crop boundary.
        slidery2 (QSlider): A slider for adjusting the bottom crop boundary.
        background_frame: The original frame for reference during cropping adjustments.

    Methods:
        - `__init__(name, instance)`: Initialize a CropTab object with a name and an instance manager.
        - `slider_changed()`: Handle changes in the crop sliders.
        - `tab_activated()`: Called when the tab is activated.
        - `tab_deactivated()`: Called when the tab is deactivated.
        - `hide_sliders()`: Hide the crop sliders.
        - `show_sliders(height, width)`: Show and configure the crop sliders.
        - `video_update()`: Abstract method for updating video content within the tab.
    """

    def __init__(self, name: str, instance: InstanceManager) -> None:
        """
        Initialize a CropTab object.

        Args:
            name : The name of the tab.
            instance : An instance manager for managing application instances and settings.
        """
        super().__init__(name, instance)
        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.image_label = QLabel()

        self.sliderx1 = QSlider(Qt.Horizontal, self)
        self.sliderx2 = QSlider(Qt.Horizontal, self)
        self.slidery1 = QSlider(Qt.Horizontal, self)
        self.slidery2 = QSlider(Qt.Horizontal, self)
        self.sliderx1.valueChanged.connect(self.slider_changed)
        self.sliderx2.valueChanged.connect(self.slider_changed)
        self.slidery1.valueChanged.connect(self.slider_changed)
        self.slidery2.valueChanged.connect(self.slider_changed)

        self.layout.addWidget(self.sliderx1)
        self.layout.addWidget(self.sliderx2)
        self.layout.addWidget(self.slidery1)
        self.layout.addWidget(self.slidery2)

        self.layout.addWidget(self.image_label)

        self.background_frame = None

        # Set the layout for the tab
        self.setLayout(self.layout)

    def slider_changed(self):
        """
        Handle changes in the crop sliders.
        """
        h, w, _ = self.background_frame.shape
        img = draw_overlay(
            self.background_frame,
            0,
            0,
            w=self.sliderx1.value(),
            h=h,
        )

        img = draw_overlay(
            img,
            w - self.sliderx2.value(),
            0,
            w=self.sliderx2.value(),
            h=h,
        )
        img = draw_overlay(
            img,
            0,
            0,
            w=w,
            h=self.slidery1.value(),
        )
        img = draw_overlay(
            img,
            0,
            h - self.slidery2.value(),
            w=w,
            h=self.slidery2.value(),
        )

        self.image_label.setPixmap(cv2qim(img))
        self.instance.settings.crop = (
            self.sliderx1.value(),
            self.sliderx2.value(),
            self.slidery1.value(),
            self.slidery2.value(),
        )

    def tab_activated(self):
        """
        Called when the tab is activated.
        """
        super().tab_activated()
        frame = self.instance.settings.next_frame
        if frame is None:
            self.image_label.setText("Please open an active Source in the Sources Tab.")
            self.hide_sliders()
            return
        self.background_frame = frame
        self.image_label.setPixmap(cv2qim(frame))
        h, w, _ = frame.shape
        self.show_sliders(h, w)

    def tab_deactivated(self):
        """
        Called when the tab is deactivated.
        """
        super().tab_deactivated()

    def hide_sliders(self):
        """
        Hide the crop sliders.
        """
        self.sliderx1.hide()
        self.slidery1.hide()
        self.slidery2.hide()
        self.sliderx2.hide()

    def show_sliders(self, height: int, width: int) -> None:
        """
        Show and configure the crop sliders.

        Args:
            height : The height of the image frame.
            width : The width of the image frame.
        """
        self.sliderx1.show()
        self.sliderx1.setMinimum(0)
        self.sliderx1.setMaximum(width)

        self.sliderx2.show()
        self.sliderx2.setMinimum(0)
        self.sliderx2.setMaximum(width)

        self.slidery1.show()
        self.slidery1.setMinimum(0)
        self.slidery1.setMaximum(height)

        self.slidery2.show()
        self.slidery2.setMinimum(0)
        self.slidery2.setMaximum(height)

        self.slider_changed()

    def video_update(self):
        """
        Abstract method for updating video content within the tab.
        """
        pass
