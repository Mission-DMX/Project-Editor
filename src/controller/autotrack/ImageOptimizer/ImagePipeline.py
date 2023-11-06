from ImageOptimizer.BasicOptimizer import (
    ResizeOptimizer,
    CropOptimizer,
    GrayScaleOptimizer,
)


class ImagePipeline:
    """
    The `ImagePipeline` class represents a sequence of image optimization steps.

    Attributes:
        steps (list): A list of optimization steps to be applied in sequence.

    Methods:
        - `add_step(step)`: Add an optimization step to the pipeline.
        - `optimize(image)`: Apply all optimization steps in the pipeline to an input image.
        - `setup()`: Configure the pipeline with a set of optimization steps.
        - `setup_processing()`: Configure the pipeline for processing.
        - `setup_preview()`: Configure the pipeline for preview.

    """

    # TODO: Add Settings checkboxes
    def __init__(self):
        self.steps = []

    def add_step(self, step):
        """
        Add an optimization step to the pipeline.

        Args:
            step (Optimizer): An instance of an image optimization step.
        """
        self.steps.append(step)

    def optimize(self, image):
        """
        Apply all optimization steps in the pipeline to an input image.

        Args:
            image (numpy.ndarray): The input image to be optimized.

        Returns:
            numpy.ndarray: The optimized image.
        """
        for step in self.steps:
            image = step.process(image)
        return image

    def setup(self):
        """
        Configure the pipeline with a set of optimization steps.

        You can uncomment and customize the optimization steps based on your requirements.
        """
        # self.add_step(ResizeOptimizer("Resize 512x512", size=(512, 512)))
        # self.add_step(CropOptimizer("Crop 100:100, 100:100", (0, 1920, 0, 1080)))
        self.add_step(GrayScaleOptimizer("Grayscale"))

    def setup_processing(self):
        """
        Configure the pipeline for processing.

        You can uncomment and customize the optimization steps for processing based on your requirements.
        """
        # self.add_step(ResizeOptimizer("Resize 512x512", size=(512, 512)))
        # self.add_step(CropOptimizer("Crop 100:100, 100:100", (0, 1920, 0, 1080)))
        # self.add_step(GrayScaleOptimizer("Grayscale"))

    def setup_preview(self):
        """
        Configure the pipeline for preview.

        You can uncomment and customize the optimization steps for preview based on your requirements.
        """
        # self.add_step(GrayScaleOptimizer("Grayscale"))
