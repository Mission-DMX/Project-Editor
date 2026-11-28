"""Preview controller for the property-based cue editor widget.

Owned by the PropertyCueEditor: bridges the editor's time cursor and
play/pause state into the :class:`PropertyCuesPreviewThread`.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer

from model.control_desk import set_seven_seg_display_content
from model.filter_data.utility import format_seconds
from model.virtual_filters.property_cues.preview_runtime import (
    PropertyCuesPreviewThread,
    build_preview_filters,
)

if TYPE_CHECKING:
    from model import Filter
    from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

logger = getLogger(__name__)


_DEFAULT_SHUTDOWN_TIMEOUT_MS = 500
# 100 ms matches the existing cue editor's visible update rate on the
# XTouch 7-seg display without taxing the GUI thread.
_SEVEN_SEG_TICK_MS = 100


def _format_seven_seg(cue_index: int, timecode_sec: float) -> str:
    """Return the 12-char XTouch 7-seg string for ``cue_index`` and ``timecode_sec``.

    Mirrors ``TimelineContentWidget._update_7seg_text`` in the existing cue
    editor so the two editors show timecodes identically: 10 pure-digit
    characters for the time (zero-padded) prefixed by the 2-digit cue index.
    """
    txt = format_seconds(max(0.0, timecode_sec)).replace(":", "").replace(".", "")
    while len(txt) < 10:
        txt = "0" + txt
    txt = str(cue_index % 100) + txt
    while len(txt) < 12:
        txt = " " + txt
    return txt


class PreviewController(QObject):
    """Holds the current :class:`PropertyCuesPreviewThread` for an editor.

    Owns a 100 ms :class:`QTimer` while the preview thread is live so the
    GUI can advance the preview's own clock, update the XTouch 7-seg
    display, and push the latest timecode into the preview thread. The
    controller is stateless beyond the owning editor's lifetime: calling
    :meth:`start` after a previous :meth:`stop` is supported and spins up
    a fresh thread (and a fresh constant-filter mapping).
    """

    def __init__(
        self,
        vfilter: PropertyBasedCueFilter,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the preview controller for the given virtual filter."""
        super().__init__(parent)
        self._vfilter = vfilter
        self._thread: PropertyCuesPreviewThread | None = None
        self._filter_list: list[Filter] = []
        self._timecode = 0.0
        self._playing = False
        self._cue_index = 0
        # Tracks the last string we pushed to the XTouch 7-seg so repeated
        # ticks with unchanged content skip the call. Every push ends up in
        # :func:`send_independent_update_msg`, which sends a full desk_update
        # protobuf to fish (including ``selected_bank = 0``). Hitting fish
        # 10 times a second with that packet triggers "Failed to change
        # active bank" errors and makes the ArtNet writer fall behind --
        # see the regression reported after wiring the preview timer.
        self._last_seven_seg_content: str | None = None
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(_SEVEN_SEG_TICK_MS)
        self._tick_timer.timeout.connect(self._on_tick)

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
        # Start the 100 ms tick that drives the preview clock and 7-seg
        # update once the thread is live; the first tick fires _SEVEN_SEG_TICK_MS
        # later. Push the initial display immediately so the user sees
        # "CC 0000000000" (or current timecode) the moment preview starts.
        self._push_seven_seg()
        self._tick_timer.start()

    def stop(self, timeout_ms: int = _DEFAULT_SHUTDOWN_TIMEOUT_MS) -> None:
        """Interrupt the preview thread and wait briefly for it to exit.

        Flipping ``in_preview_mode`` back to False here is what lets the
        editor re-serialise the show to fish in production mode: without
        it, :meth:`PropertyBasedCueFilter.instantiate_filters` keeps
        emitting the preview constant graph (including every
        ``__PREVIEW_CONST__…`` input of the postprocess chain) even
        after the preview thread is gone, and fish rejects the resulting
        scene because the cloned switch expects a uint8 ``select`` while
        the preview constant for ``pan_curvesel`` is still around.

        Hardened against teardown-time races: the tick timer is stopped
        before the preview thread is joined so a late-firing tick cannot
        poke the vfilter mid-destruction, and every attribute access on
        the vfilter is wrapped in ``RuntimeError`` catches because Qt may
        have deleted the underlying C++ object between the editor's
        ``parent_closed`` hook and the application's close event.
        """
        try:
            self._tick_timer.stop()
        except RuntimeError:
            pass
        # Blank the 7-seg so the next editor to claim it doesn't inherit
        # our preview timecode on the physical desk. Reset the dedup cache
        # too so a restart pushes a fresh value instead of noticing the
        # blank content matches and skipping the first update.
        self._last_seven_seg_content = None
        try:
            set_seven_seg_display_content(" " * 12, update_from_gui=True)
        except RuntimeError as exc:
            logger.debug("PreviewController.stop: 7-seg update failed: %s", exc)
        if self._vfilter is not None:
            try:
                self._vfilter.in_preview_mode = False
                self._vfilter._channel_mapping = {}
            except RuntimeError as exc:
                logger.debug("PreviewController.stop: vfilter gone: %s", exc)
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

    def rewind_to_start(self) -> None:
        """Pause playback and jump back to cue 0, step 0, timecode 0.0 (L11 "stop" semantics).

        The XTouch stop button maps to this: it always returns the user to
        the very top of the preview so pressing play again starts fresh,
        regardless of where playback was.
        """
        self.set_playing(False)
        self.set_cue_index(0)
        self.set_timecode(0.0)
        self._push_seven_seg()

    def toggle_playing(self) -> bool:
        """Flip playback on/off and return the new state (L11 play button semantics)."""
        self.set_playing(not self._playing)
        return self._playing

    @property
    def is_playing(self) -> bool:
        """Return True iff the preview thread is currently emitting updates."""
        return self._playing

    @property
    def cue_index(self) -> int:
        """Return the cue index the preview is currently evaluating."""
        return self._cue_index

    @property
    def timecode(self) -> float:
        """Return the current preview timecode in seconds (relative to the active cue)."""
        return self._timecode

    def set_timecode(self, seconds: float) -> None:
        """Push the editor's time cursor into the preview thread."""
        self._timecode = max(0.0, float(seconds))
        if self._thread is not None:
            self._thread.set_timecode(self._timecode)
            self._push_seven_seg()

    def set_playing(self, playing: bool) -> None:
        """Toggle whether the preview thread emits updates each tick."""
        self._playing = bool(playing)
        if self._thread is not None:
            self._thread.set_playing(self._playing)

    def set_cue_index(self, index: int) -> None:
        """Select which compiled cue the preview thread evaluates."""
        self._cue_index = max(0, int(index))
        if self._thread is not None:
            self._thread.set_cue_index(self._cue_index)
            self._push_seven_seg()

    def _on_tick(self) -> None:
        """Timer callback: advance the preview clock, push it into the thread, update 7-seg."""
        if self._thread is None:
            return
        try:
            if self._playing:
                self._timecode += _SEVEN_SEG_TICK_MS / 1000.0
                self._thread.set_timecode(self._timecode)
            self._push_seven_seg()
        except RuntimeError as exc:
            # Qt may have deleted either the thread C++ object or one of its
            # dependencies between the timer start and this tick firing;
            # stop the timer so we don't keep hitting the same stale state
            # for the rest of the application's lifetime.
            logger.debug("PreviewController._on_tick: stopping on error: %s", exc)
            try:
                self._tick_timer.stop()
            except RuntimeError:
                pass

    def _push_seven_seg(self) -> None:
        """Send the current (cue, timecode) to the XTouch 7-seg display.

        Deduplicates against :attr:`_last_seven_seg_content` so idle preview
        ticks (paused playback, no cue/step navigation) stop hitting fish
        with redundant ``desk_update`` protobufs. ``set_seven_seg_display_content``
        unconditionally emits a message carrying ``selected_bank = 0``;
        emitting it 10 times a second while the user does nothing produced
        a stream of "Failed to change active bank as it is out of range"
        errors on fish and backed the ArtNet writer up to the point of
        dropping output packets.
        """
        content = _format_seven_seg(self._cue_index, self._timecode)
        if content == self._last_seven_seg_content:
            return
        self._last_seven_seg_content = content
        set_seven_seg_display_content(content, update_from_gui=True)
