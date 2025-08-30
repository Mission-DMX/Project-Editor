# coding=utf-8
"""Methods for camera calibration and image distortion."""

import cv2
import numpy as np


class Calibration:
    """The `Calibration` class provides methods for camera calibration and image distortion correction.

    It serves as the parent class for specific calibration.
    """

    def __init__(self):
        """Camera Calibration."""
        self.camera_matrix = None
        self.distortion_coeffs = None

    def save(self, filename):
        """Save the camera matrix and distortion coefficients to a file.

        Args:
            filename: The filename without file extension.

        """
        np.savez(
            f"{filename}.npz",
            camera_matrix=self.camera_matrix,
            distortion_coeffs=self.distortion_coeffs,
        )

    def load(self, file):
        """Load the camera matrix and distortion coefficients from a file.

        Args:
            file: The filename with file extension.

        Returns: Tuple (camera_matrix, distortion_coeffs)

        """
        npzfile = np.load(file)
        return npzfile["camera_matrix"], npzfile["distortion_coeffs"]

    def undistort(self, image):
        """Undistort an image using the camera matrix and distortion coefficients, if available.

        Args:
            image: The image to undistort (distorted).

        Returns: The undistorted image.

        """
        if self.camera_matrix is not None and self.distortion_coeffs is not None:
            return cv2.undistort(
                image,
                self.camera_matrix,
                self.distortion_coeffs,
                None,
                self.camera_matrix,
            )
        else:
            return image
