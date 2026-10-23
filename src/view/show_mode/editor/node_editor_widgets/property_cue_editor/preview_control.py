"""Preview controller for the property-based cue editor widget.

Owned by the PropertyCueEditor (WP10): bridges the editor's time cursor and
play/pause state into the :class:`PropertyCuesPreviewThread` from WP12.

TODO(WP14): wire this into the editor shell created in WP10 — call
:meth:`start` from the editor's ``parent_opened`` hook (or from a dedicated
"Start Preview" button) and :meth:`stop` from its teardown path.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

from model.virtual_filters.property_cues.preview_runtime import (
    PropertyCuesPreviewThread,
    build_preview_filters,
)

if TYPE_CHECKING:
    from model import Filter
    from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

logger = getLogger(__name__)


_DEFAULT_SHUTDOWN_TIMEOUT_MS = 500


class PreviewController(QObject):
    """Holds the current :class:`PropertyCuesPreviewThread` for an editor.

    The controller is stateless beyond the owning editor's lifetime: calling
    :meth:`start` after a previous :meth:`stop` is supported and spins up a
    fresh thread (and a fresh constant-filter mapping).
    """

    def __init__(
        self,
        vfilter: PropertyBasedCueFilter,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._vfilter = vfilter
        self._thread: PropertyCuesPreviewThread | None = None
        self._filter_list: list[Filter] = []
        self._timecode = 0.0
        self._playing = False
        self._cue_index = 0

    @property
    def thread(self) -> PropertyCuesPreviewThread | None:
        """Return the currently running preview thread (or None)."""
        return self._thread

    @property
    def filter_list(self) -> list[Filter]:
        """Return the preview constant filters built on the last :meth:`start`."""
        return list(self._filter_list)

    def start(self) -> None:
        """Compute the preview channel mapping and start the preview thread.

        If a thread is already running it is first stopped so the caller can
        safely restart on model edits.
        """
        if self._thread is not None and self._thread.isRunning():
            self.stop()
        self._filter_list = []
        mapping = build_preview_filters(self._vfilter, self._vfilter.scene,
                                        self._filter_list)
        if not mapping:
            logger.debug("PreviewController.start: no channels to preview.")
            return
        self._vfilter._channel_mapping = mapping
        self._vfilter.in_preview_mode = True
        thread = PropertyCuesPreviewThread(self._vfilter, mapping, parent=self)
        thread.set_timecode(self._timecode)
        thread.set_cue_index(self._cue_index)
        thread.set_playing(self._playing)
        self._thread = thread
        thread.start()

    def stop(self, timeout_ms: int = _DEFAULT_SHUTDOWN_TIMEOUT_MS) -> None:
        """Interrupt the preview thread and wait briefly for it to exit."""
        thread = self._thread
        if thread is None:
            return
        try:
            if thread.isRunning():
                thread.requestInterruption()
                thread.wait(timeout_ms)
        except RuntimeError as exc:
            logger.debug("PreviewController.stop: thread already gone: %s", exc)
        self._thread = None

    def set_timecode(self, seconds: float) -> None:
        """Push the editor's time cursor into the preview thread."""
        self._timecode = float(seconds)
        if self._thread is not None:
            self._thread.set_timecode(self._timecode)

    def set_playing(self, playing: bool) -> None:
        """Toggle whether the preview thread emits updates each tick."""
        self._playing = bool(playing)
        if self._thread is not None:
            self._thread.set_playing(self._playing)

    def set_cue_index(self, index: int) -> None:
        """Select which compiled cue the preview thread evaluates."""
        self._cue_index = int(index)
        if self._thread is not None:
            self._thread.set_cue_index(self._cue_index)
