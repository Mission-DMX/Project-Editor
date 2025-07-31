import os

import cv2
import numpy as np

from controller.autotrack.Helpers.ImageHelper import draw_bounding_box
from controller.utils.yaml import yaml_load
from utility import resource_path

CLASSES = yaml_load(resource_path(os.path.join("resources", "autotrack_models", "coco128.yaml")))["names"]
colors = np.random.uniform(0, 255, size=(len(CLASSES), 3))


def _apply_nms(boxes, scores):
    result_boxes = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45, 0.5)
    return result_boxes


def _create_detections(result_boxes, boxes, scores, class_ids, scale):
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


def post_process_yolov8_output(output, confidence_threshold=0.5):
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


def draw_boxes(frame, detections, scale):
    """This method draws bounding boxes inside the frame for human inspection.

    :param frame: The frame to draw in
    :param detections: The detections array
    :param scale: The size of the rectangle
    """
    for detection in detections:
        # print(detection)
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


def get_filtered_detections(outputs, scale: int, confidence_threshold: float):
    boxes = []
    scores = []
    class_ids = []

    for i in range(outputs.shape[1]):
        classes_scores = outputs[0][i][4:]
        (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(
            classes_scores
        )
        if (
                maxScore >= confidence_threshold
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

    result_boxes = _apply_nms(boxes, scores)
    detections = _create_detections(
        result_boxes, boxes, scores, class_ids, scale
    )
    return detections


def process(outputs: np.ndarray, scale: float) -> list[dict[str, int]]:
    scores = []
    boxes = []
    for i in range(8400):
        scores.append(outputs[4][i])
        boxes.append([outputs[0][i], outputs[1][i], outputs[2][i], outputs[3][i]])
    result_boxes = _apply_nms(boxes, scores)
    print(f"Humans found: {result_boxes}")
    detections: list[dict[str, int]] = []
    for i in range(len(result_boxes)):
        index = result_boxes[i]
        box = boxes[index]
        detection: dict[str, int] = {
            "class_id": 0,
            "class_name": CLASSES[0],
            "confidence": scores[index],
            "box": box,
            "scale": scale,
        }
        detections.append(detection)
    return detections
