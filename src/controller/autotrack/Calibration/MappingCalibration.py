import cv2
import numpy as np


class MappingCalibration:
    def __init__(self, points: list[tuple[tuple[int, int], tuple[int, int]]]):
        obj_points = []
        img_points = []
        for i in points:
            obj_points.append(i[0])
            img_points.append(i[1])
        src_points = np.array(img_points, dtype=np.float32)
        dst_points = np.array(obj_points, dtype=np.float32)
        self.M, _ = cv2.findHomography(src_points, dst_points, method=cv2.RANSAC)

    def get_point(self, point: tuple[int, int]) -> tuple[int, int]:
        """
        This method transforms a point received as coordinates within the camera frame into Pan/Tilt coordinates for the moving head.

        :param point: The position of the person relative to the frame
        :returns: The position of the person expressed in moving head coordinates
        """
        x, y = point
        pt = np.array([[x, y]], dtype=np.float32)
        transformed_point = cv2.perspectiveTransform(pt.reshape(-1, 1, 2), self.M)
        c = (int(transformed_point[0][0][0]), int(transformed_point[0][0][1]))
        return c
