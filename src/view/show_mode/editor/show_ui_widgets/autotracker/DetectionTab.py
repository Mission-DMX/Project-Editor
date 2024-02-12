import asyncio

from controller.autotrack.Detection.VideoProcessor import draw_boxes, process
from controller.autotrack.Detection.Yolo8.Yolo8GPU import Yolo8GPU
from view.show_mode.editor.show_ui_widgets.autotracker.GuiTab import GuiTab
from controller.autotrack.Helpers.ImageHelper import cv2qim
from controller.autotrack.Helpers.InstanceManager import InstanceManager
from PySide6.QtWidgets import (
    QGridLayout,
    QLayout,
    QLabel,
    QCheckBox,
)

from controller.autotrack.ImageOptimizer.BasicOptimizer import CropOptimizer


class DetectionTab(GuiTab):
    def __init__(self, name, instance: InstanceManager):
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

    def tab_activated(self):
        super().tab_activated()
        if self.yolo8 is None:
            self.yolo8 = Yolo8GPU()
        self.video_update()

    def video_update(self):
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

    def process_frame(self, frame):
        h, w, *_ = frame.shape
        length = max(h, w)
        scale = length / 640

        self.background_frame = frame
        outputs = self.yolo8.detect(self.background_frame)
        # detections = self.get_filtered_detections(outputs, scale, self.get_confidence_threshold())
        detections = process(outputs, scale)
        return scale, detections

    def get_confidence_threshold(self):
        return float(self.instance.settings.settings["confidence_threshold"].text())

    def move_lights(self, detections, frame):
        if len(detections) > 0:
            max_detection = max(detections, key=lambda arr: arr["confidence"])
            # h, w, _ = frame.shape
            x1, y1, x2, y2 = max_detection["box"]
            p = (int(x1 + (x2 - x1) / 2), int(y1 + (y2 - y1) / 2))
            print(f"{p}")
            # c = ImageHelper.map_image(x, y, w, h, self.instance.settings.lights.corners)
            c = self.instance.settings.map.get_point(p)
            asyncio.run(self._asy_mouse(c))

    async def _asy_mouse(self, pos):
        await self.instance.settings.lights.set_position(pos)
