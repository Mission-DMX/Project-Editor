# coding=utf-8
import cv2
import numpy as np
import qimage2ndarray
from PySide6.QtGui import QPixmap

from controller.utils.yaml import yaml_load


def cv2qim(frame):
    """
    Convert a numpy image array (BGR) to a QPixmap (RGB).

    Args:
        frame (numpy.ndarray): The input image in BGR format.

    Returns:
        QPixmap: The converted image as a QPixmap in RGB format.
    """
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = qimage2ndarray.array2qimage(frame)
    return QPixmap.fromImage(image)


def draw_overlay(frame, x, y, w, h):
    """
    Draw a filled rectangle overlay on an image.

    Args:
        frame (numpy.ndarray): The input image.
        x (int): X-coordinate of the top-left corner of the rectangle.
        y (int): Y-coordinate of the top-left corner of the rectangle.
        w (int): Width of the rectangle.
        h (int): Height of the rectangle.

    Returns:
        numpy.ndarray: The image with the filled rectangle overlay.
    """
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 100, 0), thickness=cv2.FILLED)
    return cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)


# From YOLO8 example
def draw_bounding_box(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    """
    Draws bounding boxes on the input image based on the provided arguments.

    Args:
        img (numpy.ndarray): The input image to draw the bounding box on.
        class_id (int): Class ID of the detected object.
        confidence (float): Confidence score of the detected object.
        x (int): X-coordinate of the top-left corner of the bounding box.
        y (int): Y-coordinate of the top-left corner of the bounding box.
        x_plus_w (int): X-coordinate of the bottom-right corner of the bounding box.
        y_plus_h (int): Y-coordinate of the bottom-right corner of the bounding box.
    """
    CLASSES = yaml_load("coco128.yaml")["names"]
    colors = np.random.uniform(0, 255, size=(len(CLASSES), 3))
    label = f"{CLASSES[class_id]} ({confidence:.2f})"
    color = colors[class_id]
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
    cv2.circle(
        img, (int(x + (x_plus_w - x) / 2), int(y + (y_plus_h - y) / 2)), 5, color, 2
    )
    cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def map_image(x, y, image_x, image_y, corners):
    x1 = x / image_x
    y1 = y / image_y
    x2 = int((corners[1][0] - corners[0][0]) * x1 + corners[0][0])
    y2 = int((corners[2][1] - corners[0][1]) * y1 + corners[0][1])
    print(f"{x2}:{y2}")
    return [x2, y2]
