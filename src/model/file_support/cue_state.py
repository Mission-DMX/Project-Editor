"""Contains cue state model."""

import datetime as dt
from enum import Enum

from tzlocal import get_localzone

import proto.FilterMode_pb2
from model import Filter


class State(Enum):
    """The state an active cue might be in."""

    STOP = 1
    PLAY = 2
    PAUSE = 3


class CueState:
    """POD class for a cue state mapping."""

    __slots__ = ("_active_cue", "_end_time", "_filter", "_paused_time", "_start_time", "_state", "_time_scale")

    def __init__(self, filter_: Filter) -> None:
        """Initialize the state tracker for the given cue filter.

        The cue is initialized in the stopped state with the active cue index set to 0,
        a default end time of 20 seconds and a time scale of 1.

        :param filter_: The cue filter whose playback state this instance mirrors.
        """
        self._filter = filter_
        self._state = State.STOP
        self._end_time = dt.timedelta(seconds=float(20))
        self._paused_time = dt.timedelta(seconds=float(0))
        self._active_cue = 0
        self._time_scale = 1
        self._start_time = dt.datetime.now(tz=get_localzone())

    @property
    def playing_cue(self) -> int:
        """Return the index of the currently playing cue.

        :returns: The active cue index while in the play state, or ``-1`` when the cue
            is stopped or paused.
        """
        return self._active_cue if self._state == State.PLAY else -1

    def __str__(self) -> str:
        """Get a human readable representation of the current state.

        The format depends on the state: ``"stopped"`` when stopped, otherwise either
        the paused position or the elapsed playback time (scaled by ``_time_scale``),
        followed by the end time and the active cue index.

        :returns: A formatted status string suitable for display to the user.
        """
        ret = ""
        if self._state == State.STOP:
            return "stopped"

        if self._state == State.PAUSE:
            ret = "paused at " + self.time_delta_to_str(self._paused_time)
        if self._state == State.PLAY:
            ret = self.time_delta_to_str(
                (dt.datetime.now(tz=get_localzone()) - self._start_time) * self._time_scale
            )
        return ret + " / " + self.time_delta_to_str(self._end_time) + " in cue " + str(self._active_cue)

    def update(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Update the state representation from a received fish update message.

        The ``parameter_value`` is a semicolon-separated string with five fields in order:
        the state keyword (``play``, ``pause`` or ``stop``), the active cue index, the
        current playback position in seconds, the cue end time in seconds and the time
        scale factor.

        :param param: The fish update parameter carrying the new cue state.
        """
        values = param.parameter_value.split(";")
        self._start_time = dt.datetime.now(tz=get_localzone()) - dt.timedelta(seconds=float(values[2]))
        self._end_time = dt.timedelta(seconds=float(values[3]))
        self._active_cue = int(values[1])
        self._time_scale = float(values[4])
        if values[0] == "play":
            self._state = State.PLAY
        elif values[0] == "pause":
            self._paused_time = dt.timedelta(seconds=float(values[2]))
            self._state = State.PAUSE
        elif values[0] == "stop":
            self._state = State.STOP

    def time_delta_to_str(self, delta: dt.timedelta) -> str:
        """Format the time delta of the cue.

        The granularity of the output adapts to the length of ``_end_time``: days and
        hours are only emitted when the end time reaches them, while seconds and
        hundredths of a second are only emitted for shorter cues. This keeps the
        rendered string aligned with the resolution the user cares about.

        :param delta: The time delta to render relative to the current cue.
        :returns: The delta formatted as ``"[Dd ][HH:]MM[:SS[.hh]]"``.
        """
        ret = ""
        if self._end_time >= dt.timedelta(days=1):
            days = int(delta.total_seconds() / 86400)
            ret += f"{days:01d}" + "d "
            delta -= dt.timedelta(days=days)
        if self._end_time >= dt.timedelta(hours=1):
            hours = int(delta.total_seconds() / 3600)
            ret += f"{hours:02d}" + ":"
            delta -= dt.timedelta(hours=hours)
        # if self._end_time >= dt.timedelta(minutes=1):
        minutes = int(delta.total_seconds() / 60)
        ret += f"{minutes:02d}"
        delta -= dt.timedelta(minutes=minutes)
        if self._end_time < dt.timedelta(days=1):
            seconds = int(delta.total_seconds())
            ret += ":" + f"{seconds:02d}"
            delta -= dt.timedelta(seconds=seconds)
        if self._end_time < dt.timedelta(hours=1):
            ret += "." + f"{int(delta.total_seconds() * 100):02d}"
        return ret
