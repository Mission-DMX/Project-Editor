import asyncio
import threading
from logging import getLogger

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QGridLayout, QLabel, QLayout, QPushButton, QSlider

from controller.autotrack.Calibration.MappingCalibration import MappingCalibration
from controller.autotrack.Helpers.ImageHelper import cv2qim
from controller.autotrack.Helpers.InstanceManager import InstanceManager
from view.show_mode.show_ui_widgets.autotracker.gui_tab import GuiTab

logger = getLogger(__name__)


class LightSetupTab(GuiTab):
    def __init__(self, name: str, instance: InstanceManager) -> None:
        super().__init__(name, instance)
        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.image_label = QLabel()

        self._calibration_running = False
        self._calibration_step: int = 0
        self._calibration_points = [
            [(75.16666666666667, 54.0), (187, 176)],
            [(75.16666666666667, 47.0), (152, 272)],
            [(75.16666666666667, 40.0), (124, 364)],
            [(75.16666666666667, 33.0), (91, 477)],
            [(75.16666666666667, 26.0), (59, 588)],
            [(82.33333333333333, 54.0), (419, 230)],
            [(82.33333333333333, 47.0), (406, 324)],
            [(82.33333333333333, 40.0), (391, 423)],
            [(82.33333333333333, 33.0), (370, 517)],
            [(82.33333333333333, 26.0), (343, 588)],
            [(89.5, 54.0), (619, 244)],
            [(89.5, 47.0), (617, 339)],
            [(89.5, 40.0), (621, 436)],
            [(89.5, 33.0), (611, 528)],
            [(89.5, 26.0), (616, 613)],
            [(96.66666666666667, 54.0), (830, 236)],
            [(96.66666666666667, 47.0), (843, 321)],
            [(96.66666666666667, 40.0), (854, 420)],
            [(96.66666666666667, 33.0), (865, 523)],
            [(96.66666666666667, 26.0), (876, 642)],
            [(103.83333333333334, 54.0), (1069, 168)],
            [(103.83333333333334, 47.0), (1111, 280)],
            [(103.83333333333334, 40.0), (1124, 378)],
            [(103.83333333333334, 33.0), (1148, 497)],
            [(103.83333333333334, 26.0), (0, 0)],
        ]

        if self._calibration_points is not None:
            self.instance.settings.map = MappingCalibration(self._calibration_points)

        self.last_image = None

        self.sliderx1 = QSlider(Qt.Horizontal, self)
        self.sliderx2 = QSlider(Qt.Horizontal, self)
        self.slidery1 = QSlider(Qt.Horizontal, self)
        self.slidery2 = QSlider(Qt.Horizontal, self)
        self.sliderx1.valueChanged.connect(self.slider_changed)
        self.sliderx2.valueChanged.connect(self.slider_changed)
        self.slidery1.valueChanged.connect(self.slider_changed)
        self.slidery2.valueChanged.connect(self.slider_changed)

        self.btn_top_left = QPushButton("Top Left", self)
        self.btn_top_right = QPushButton("Top Right", self)
        self.btn_bottom_left = QPushButton("Bottom Left", self)
        self.btn_bottom_right = QPushButton("Bottom Right", self)
        self.btn_frame = QPushButton("Frame", self)
        self.btn_calibrate = QPushButton("Calibrate", self)

        self.buttons = [
            self.btn_top_left,
            self.btn_top_right,
            self.btn_bottom_left,
            self.btn_bottom_right,
        ]

        self.layout.addWidget(self.btn_top_left)
        self.layout.addWidget(self.btn_top_right)
        self.layout.addWidget(self.btn_bottom_left)
        self.layout.addWidget(self.btn_bottom_right)

        self.layout.addWidget(self.btn_frame)

        self.layout.addWidget(self.btn_calibrate)

        self.layout.addWidget(self.sliderx1)
        self.layout.addWidget(self.sliderx2)
        self.layout.addWidget(self.slidery1)
        self.layout.addWidget(self.slidery2)

        self.btn_top_left.clicked.connect(self.btn_position_pressed)
        self.btn_top_right.clicked.connect(self.btn_position_pressed)
        self.btn_bottom_left.clicked.connect(self.btn_position_pressed)
        self.btn_bottom_right.clicked.connect(self.btn_position_pressed)

        self.btn_calibrate.clicked.connect(self.calibrate_points)

        self.btn_frame.clicked.connect(self.btn_frame_pressed)

        self.layout.addWidget(self.image_label)

        self.background_frame = None

        # Connect the mousePressEvent event to a custom slot function
        self.image_label.mousePressEvent = self.mouse_clicked

        # Set the layout for the tab
        self.setLayout(self.layout)

    def btn_frame_pressed(self) -> None:
        # asyncio.run(self._async_btn_frame_pressed())
        # asyncio.get_event_loop().create_task(self._async_btn_frame_pressed())
        thread = threading.Thread(target=self.worker_thread)
        thread.start()

    def setup_calibration(self) -> None:
        grid_size = 5
        self._calibration_points = []
        corners = self.instance.settings.lights.corners
        x = corners[0][0]
        y = corners[0][1]
        w = (corners[1][0] - x) / (grid_size + 1)
        h = (corners[2][1] - y) / (grid_size + 1)
        for i in range(grid_size):
            for j in range(grid_size):
                item = [((1 + i) * w + x, (1 + j) * h + y), (0, 0)]
                self._calibration_points.append(item)
        logger.info(self._calibration_points)

    async def _async_btn_frame_pressed(self) -> None:
        await self.instance.settings.lights.frame(
            2000, self.instance.settings.lights.corners,
        )

    def worker_thread(self) -> None:
        # Create a new event loop for this worker thread
        event_loop = asyncio.new_event_loop()

        # Set the event loop as current for this thread
        asyncio.set_event_loop(event_loop)

        # Define an asyncio function to run in the worker thread
        async def my_async_function(self_: LightSetupTab) -> None:
            await self_.instance.settings.lights.frame(
                2000, self_.instance.settings.lights.corners,
            )
            logger.info("Asyncio code running in worker thread")

        # Run the asyncio function
        event_loop.run_until_complete(my_async_function(self))
        event_loop.close()

    def btn_position_pressed(self) -> None:
        button = self.sender()
        self.instance.settings.lights.corners[self.buttons.index(button)] = [
            self.sliderx1.value(),
            self.sliderx2.value(),
        ]
        logger.info("Button %s gedrückt", self.buttons.index(button))
        logger.info(self.instance.settings.lights.corners)

    def slider_changed(self) -> None:
        asyncio.run(self._async_slider())

    async def _async_slider(self) -> None:
        await self.instance.settings.lights.set_position(
            [self.sliderx1.value(), self.sliderx2.value()],
        )
        await self.instance.settings.lights.set_brightness(self.slidery1.value())

    def mouse_clicked(self, event: QMouseEvent) -> None:
        if self.last_image is not None:
            if self._calibration_running:
                self.mouse_calibration(event)
            else:
                self.light_to_mouse(event)

    def light_to_mouse(self, event: QMouseEvent) -> None:
        click_position = event.pos()
        x, y = click_position.x(), click_position.y()

        # Display the position in the console
        logger.info("Mouse clicked at position (x: %d, y: %d)", x, y)

        # h, w, _ = self.last_image.shape

        # c = ImageHelper.map_image(x, y, w, h, self.instance.settings.lights.corners)
        c = self.instance.settings.map.get_point((x, y))
        asyncio.run(self._asy_mouse(c))

    async def _asy_mouse(self, pos: tuple[int, int]) -> None:
        await self.instance.settings.lights.set_position(pos)

    def tab_activated(self) -> None:
        """
        Called when the tab is activated.
        """
        super().tab_activated()

        self.show_sliders(255, 255)

    def tab_deactivated(self) -> None:
        """
        Called when the tab is deactivated.
        """
        super().tab_deactivated()

    def hide_sliders(self) -> None:
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

    def video_update(self) -> None:
        """
        Update the video content within the tab.
        """
        frame = self.instance.settings.next_frame
        if frame is not None and self.active:
            frame = self.instance.get_preview_pipeline().optimize(frame)
            self.last_image = frame
            self.image_label.setPixmap(cv2qim(frame))

    def calibrate_points(self) -> None:
        if self.instance.settings.lights.corners:
            self.setup_calibration()
            self._calibration_step = 0
            self._calibration_running = True
            self.move_calibration_light(0)

    def mouse_calibration(self, event: QMouseEvent) -> None:
        click_position = event.pos()
        x, y = click_position.x(), click_position.y()
        self._calibration_points[self._calibration_step][1] = (x, y)
        self._calibration_step = self._calibration_step + 1
        self.move_calibration_light(self._calibration_step)
        logger.info(self._calibration_points)
        logger.info("%s:%s", self._calibration_step, len(self._calibration_points))
        if self._calibration_step >= len(self._calibration_points) - 1:
            self._calibration_running = False
            self.instance.settings.map = MappingCalibration(self._calibration_points)

    def move_calibration_light(self, pos: int) -> None:
        x, y = self._calibration_points[pos][0]
        p = [x, y]
        asyncio.run(self._asy_mouse(p))
