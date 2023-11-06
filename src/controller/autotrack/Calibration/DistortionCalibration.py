import cv2

from controller.autotrack.Calibration.Calibration import Calibration


class DistortionCalibration(Calibration):
    """
    DistortionCalibration is a class for performing camera calibration
    using a chessboard pattern and correcting image distortion.


    Args:
        images (list): List of input images for calibration.
        file (str): File to load camera matrix and distortion coefficients from (optional).

    Attributes:
        camera_matrix (numpy.ndarray): The camera matrix after calibration.
        distortion_coeffs (numpy.ndarray): The distortion coefficients after calibration.
    """

    def __init__(self, images=None, file=None):
        super().__init__()
        self.images = images
        if file is None and images is not None:
            self.camera_matrix, self.distortion_coeffs = self.chessboard_calibration()
        if file is not None:
            self.camera_matrix, self.distortion_coeffs = self.load(file)

    def chessboard_calibration(self):
        """
        Perform camera calibration using a chessboard pattern.

        :return: Tuple containing camera matrix and distortion coefficients.
        """
        obj_points = []
        img_points = []
        for image in self.images:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (9, 9), None)
            if ret:
                img_points.append(corners)
                # TODO Add object_borders points via gui
            if img_points:
                (
                    ret,
                    camera_matrix,
                    distortion_coeffs,
                    rvecs,
                    tvecs,
                ) = cv2.calibrateCamera(
                    obj_points, img_points, gray.shape[::-1], None, None
                )
                return camera_matrix, distortion_coeffs
            else:
                return None, None
