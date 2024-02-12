from controller.autotrack.Helpers.AutoTrackerSettings import AutoTrackerSettings
from controller.autotrack.ImageOptimizer.ImagePipeline import ImagePipeline
from controller.autotrack.Sources.Loader import Loader
from model.virtual_filters import AutoTrackerFilter


class InstanceManager:
    """
    The `InstanceManager` class manages instances and settings within the application.

    Attributes:
        loader (Loader): The data loader instance.
        preview_pipeline (ImagePipeline): The image preview pipeline instance.
        processing_pipeline (ImagePipeline): The image processing pipeline instance.
        _settings (AutoTrackerSettings): The application settings.
    """

    # TODO refactor to Properties
    def __init__(self, f: AutoTrackerFilter):
        self.loader = None
        self.preview_pipeline: ImagePipeline | None = None
        self.processing_pipeline: ImagePipeline | None = None
        self._settings = AutoTrackerSettings(f)
        self.filter: AutoTrackerFilter = f
        for setting, value in f.filter_configurations.items():
            self._settings.settings[setting] = value

    def set_loader(self, loader: Loader):
        self.loader = loader

    def set_preview_pipeline(self, prp: ImagePipeline):
        self.preview_pipeline = prp

    def set_processing_pipeline(self, ppp: ImagePipeline):
        self.processing_pipeline = ppp

    def get_loader(self):
        return self.loader

    def get_preview_pipeline(self) -> ImagePipeline:
        prp = self.preview_pipeline
        if prp is None:
            prp = ImagePipeline()
            prp.setup_preview()
            self.set_preview_pipeline(prp)
        return self.preview_pipeline

    def get_processing_pipeline(self) -> ImagePipeline:
        prp = self.processing_pipeline
        if prp is None:
            prp = ImagePipeline()
            prp.setup_processing()
            self.set_processing_pipeline(prp)
        return self.processing_pipeline

    @property
    def settings(self):
        """
        Get the application settings.

        Returns:
            AutoTrackerSettings: The application settings.
        """
        return self._settings
