"""Calibration for auto track Camera."""

# coding=utf-8
from typing import override

import cv2
import numpy as np


def _parse_parameters(str_representation: str) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    param_list = []
    for p_str in str_representation.split(";"):
        p_parts = p_str.split(",")
        for i in range(p_parts):
            p_parts[i] = int(p_parts[i])
        param_list.append(((p_parts[0], p_parts[1]), (p_parts[2], p_parts[3])))
    return param_list


class MappingCalibration:
    """Calibration for auto track Camera."""

    def __init__(self, points: list[tuple[tuple[int, int], tuple[int, int]]] | str):
        """Calibration for auto track Camera."""
        if isinstance(points, str):
            points = _parse_parameters(points)
        self._original_representation = points
        obj_points = []
        img_points = []
        for i in points:
            obj_points.append(i[0])
            img_points.append(i[1])
        src_points = np.array(img_points, dtype=np.float32)
        dst_points = np.array(obj_points, dtype=np.float32)
        self.M, _ = cv2.findHomography(src_points, dst_points, method=cv2.RANSAC)

    def get_point(self, point: tuple[int, int]) -> tuple[int, int]:
        """Transform a point received as coordinates within the camera frame into Pan/Tilt coordinates for the moving head.

        Args:
            point: The position of the person relative to the frame

        Returns: The position of the person expressed in moving head coordinates

        """
        x, y = point
        pt = np.array([[x, y]], dtype=np.float32)
        transformed_point = cv2.perspectiveTransform(pt.reshape(-1, 1, 2), self.M)
        c = (int(transformed_point[0][0][0]), int(transformed_point[0][0][1]))
        return c

    @override
    def __str__(self):
        def generate_representation(p: tuple[tuple[int, int], tuple[int, int]]) -> str:
            return ",".join([str(p[0][0]), str(p[0][1]), str(p[1][0]), str(p[1][1])])

        return ";".join([generate_representation(p) for p in self._original_representation])
