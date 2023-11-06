import asyncio

import cv2
import numpy as np
from ultralytics.utils import yaml_load
from ultralytics.utils.checks import check_yaml

from Detection.Yolo8.Yolo8 import Yolo8
from Detection.Yolo8.Yolo8GPU import Yolo8GPU
from Gui.GuiTab import GuiTab
from Helpers import ImageHelper
from Helpers.ImageHelper import draw_bounding_box, cv2qim
from Helpers.InstanceManager import InstanceManager
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QLayout,
    QLabel,
    QSlider,
    QCheckBox,
)

from ImageOptimizer.BasicOptimizer import CropOptimizer

CLASSES = yaml_load(check_yaml("coco128.yaml"))["names"]
colors = np.random.uniform(0, 255, size=(len(CLASSES), 3))


CLASSES = yaml_load(check_yaml("coco128.yaml"))["names"]
colors = np.random.uniform(0, 255, size=(len(CLASSES), 3))


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
            self.draw_boxes(frame, detections, scale)
            self.image_label.setPixmap(cv2qim(frame))
            if self.swt_detection.isChecked():
                self.move_lights(detections, frame)

    def process_frame(self, frame):
        h, w, *_ = frame.shape
        length = max(h, w)
        scale = length / 640

        self.background_frame = frame
        outputs = self.yolo8.detect(self.background_frame)
        # detections = self.get_filtered_detections(outputs, scale)
        detections = self.process(outputs, scale)
        return scale, detections

    def process(self, outputs, scale):
        scores = []
        boxes = []
        for i in range(8400):
            scores.append(outputs[4][i])
            boxes.append([outputs[0][i], outputs[1][i], outputs[2][i], outputs[3][i]])
        result_boxes = self.apply_nms(boxes, scores)
        print(f"Humans found: {result_boxes}")
        detections = []
        for i in range(len(result_boxes)):
            index = result_boxes[i]
            box = boxes[index]
            detection = {
                "class_id": 0,
                "class_name": CLASSES[0],
                "confidence": scores[index],
                "box": box,
                "scale": scale,
            }
            detections.append(detection)
        return detections

    def post_process_yolov8_output(self, output, confidence_threshold=0.5):
        # Flatten and reshape the output
        predictions = output.reshape(
            -1, 84
        )  # Assuming there are 85 values per detection (adjust if needed)

        # Initialize lists to store the filtered and sorted detections
        filtered_detections = []

        # Iterate through all predictions
        for prediction in predictions:
            # Extract class confidence and bounding box coordinates
            class_confidence = prediction[4]  # Confidence score for the detected class
            if class_confidence < confidence_threshold:
                continue  # Skip detections with low confidence

            # You can also extract other information like class IDs and bounding box coordinates if needed
            class_id = np.argmax(
                prediction[5:]
            )  # Assuming class IDs start from index 5
            bounding_box = prediction[
                0:4
            ]  # Assuming bounding box coordinates are in the first 4 values

            # Append the filtered detection to the list
            filtered_detections.append(
                {
                    "class_id": class_id,
                    "confidence": class_confidence,
                    "bounding_box": bounding_box,
                }
            )

        # Sort the detections by confidence in descending order
        sorted_detections = sorted(
            filtered_detections, key=lambda x: x["confidence"], reverse=True
        )

        return sorted_detections

    def get_filtered_detections(self, outputs, scale):
        boxes = []
        scores = []
        class_ids = []

        for i in range(outputs.shape[1]):
            classes_scores = outputs[0][i][4:]
            (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(
                classes_scores
            )
            if (
                maxScore >= self.get_confidence_threshold()
                and CLASSES[maxClassIndex] == "person"
            ):
                box = [
                    outputs[0][i][0] - (0.5 * outputs[0][i][2]),
                    outputs[0][i][1] - (0.5 * outputs[0][i][3]),
                    outputs[0][i][2],
                    outputs[0][i][3],
                ]
                boxes.append(box)
                scores.append(maxScore)
                class_ids.append(maxClassIndex)

        result_boxes = self.apply_nms(boxes, scores)
        detections = self.create_detections(
            result_boxes, boxes, scores, class_ids, scale
        )
        return detections

    def apply_nms(self, boxes, scores):
        result_boxes = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45, 0.5)
        return result_boxes

    def create_detections(self, result_boxes, boxes, scores, class_ids, scale):
        detections = []
        for i in range(len(result_boxes)):
            index = result_boxes[i]
            box = boxes[index]
            detection = {
                "class_id": class_ids[index],
                "class_name": CLASSES[class_ids[index]],
                "confidence": scores[index],
                "box": box,
                "scale": scale,
            }
            detections.append(detection)
        return detections

    def draw_boxes(self, frame, detections, scale):
        for detection in detections:
            print(detection)
            # draw_bounding_box(
            #    frame,
            #   detection["class_id"],
            #  detection["confidence"],
            # round(detection["box"][0] * scale),
            # round(detection["box"][1] * scale),
            # round((detection["box"][0] + detection["box"][2]) * scale),
            # round((detection["box"][1] + detection["box"][3]) * scale),
            # )
            x, y, w, h = detection["box"]
            x1 = round((x - w / 2) * scale)
            y1 = round((y - h / 2) * scale)
            x2 = round((x + w / 2) * scale)
            y2 = round((y + h / 2) * scale)
            detection["box"] = [x1, y1, x2, y2]
            draw_bounding_box(
                frame, detection["class_id"], detection["confidence"], x1, y1, x2, y2
            )

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
