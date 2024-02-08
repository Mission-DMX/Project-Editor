import cv2
import numpy as np


class Calibration:
    """
    The `Calibration` class provides methods for camera calibration and image distortion correction. It serves as the parent class for specific calibration.

    Attributes:
        camera_matrix (numpy.ndarray): The camera matrix after calibration.
        distortion_coeffs (numpy.ndarray): The distortion coefficients after calibration.

    Methods:
        - `save(filename)`: Save the camera matrix and distortion coefficients to a file.
        - `load(file)`: Load the camera matrix and distortion coefficients from a file.
        - `undistort(image)`: Undistort an image using the camera matrix and distortion coefficients, if available.
    """

    def __init__(self):
        self.camera_matrix = None
        self.distortion_coeffs = None

    def save(self, filename):
        """
        Save the camera matrix and distortion coefficients to a file.

        :param filename: The filename without file extension.
        """
        np.savez(
            f"{filename}.npz",
            camera_matrix=self.camera_matrix,
            distortion_coeffs=self.distortion_coeffs,
        )

    def load(self, file):
        """
        Load the camera matrix and distortion coefficients from a file.

        :param file: The filename with file extension.
        :return: Tuple (camera_matrix, distortion_coeffs)
        """
        npzfile = np.load(file)
        return npzfile["camera_matrix"], npzfile["distortion_coeffs"]

    def undistort(self, image):
        """
        Undistort an image using the camera matrix and distortion coefficients, if available.

        :param image: The image to undistort (distorted).
        :return: The undistorted image.
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
