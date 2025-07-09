import asyncio
from logging import getLogger

import numpy as np
from PySide6.QtWidgets import QCheckBox, QGridLayout, QLabel, QLayout

from controller.autotrack.Detection.VideoProcessor import draw_boxes, process
from controller.autotrack.Detection.Yolo8.Yolo8GPU import Yolo8GPU
from controller.autotrack.Helpers.ImageHelper import cv2qim
from controller.autotrack.Helpers.InstanceManager import InstanceManager
from controller.autotrack.ImageOptimizer.BasicOptimizer import CropOptimizer
from view.show_mode.show_ui_widgets.autotracker.GuiTab import GuiTab

logger = getLogger(__name__)


class DetectionTab(GuiTab):
    def __init__(self, name: str, instance: InstanceManager) -> None:
        super().__init__(name, instance)
        self.background_frame = None
        self.yolo8 = None

        self.swt_detection = QCheckBox("Detection Switch")

        self.layout = QGridLayout()
        self.layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.layout.addWidget(self.swt_detection)
        self.image_label = QLabel()
        self.layout.addWidget(self.image_label)
        self.setLayout(self.layout)

    def tab_activated(self) -> None:
        super().tab_activated()
        if self.yolo8 is None:
            self.yolo8 = Yolo8GPU()
        self.video_update()

    def video_update(self) -> None:
        frame = self.instance.settings.next_frame
        if frame is None:
            self.image_label.setText("Please open an active Source in the Sources Tab.")
            return
        if self.active:
            crop = self.instance.settings.crop
            frame = self.instance.get_preview_pipeline().optimize(frame)
            h, w, *_ = frame.shape
            frame = CropOptimizer(
                "crop", (crop[2], h - crop[3], crop[0], w - crop[1])
            ).process(frame)
            scale, detections = self.process_frame(frame)
            draw_boxes(frame, detections, scale)
            self.image_label.setPixmap(cv2qim(frame))
            if self.swt_detection.isChecked():
                self.move_lights(detections, frame)

    def process_frame(self, frame: np.ndarray) -> tuple[float, list[dict[str, int]]]:
        h, w, *_ = frame.shape
        length = max(h, w)
        scale = length / 640

        self.background_frame = frame
        outputs: np.ndarray = self.yolo8.detect(self.background_frame)
        # detections = self.get_filtered_detections(outputs, scale, self.get_confidence_threshold())
        detections: list[dict[str, int]] = process(outputs, scale)
        return scale, detections

    def get_confidence_threshold(self) -> float:
        return float(self.instance.settings.settings["confidence_threshold"].text())

    def move_lights(self, detections: list[dict[str, int]], frame: np.ndarray) -> None:
        if len(detections) > 0:
            max_detection = max(detections, key=lambda arr: arr["confidence"])
            # h, w, _ = frame.shape
            x1, y1, x2, y2 = max_detection["box"]
            p = (int(x1 + (x2 - x1) / 2), int(y1 + (y2 - y1) / 2))
            logger.info(str(p))
            # c = ImageHelper.map_image(x, y, w, h, self.instance.settings.lights.corners)
            c = self.instance.settings.map.get_point(p)
            asyncio.run(self._asy_mouse(c))

    async def _asy_mouse(self, pos: tuple[int, int]) -> None:
        await self.instance.settings.lights.set_position(pos)
