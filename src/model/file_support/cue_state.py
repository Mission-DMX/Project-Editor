import datetime
from enum import Enum

from tzlocal import get_localzone

import proto.FilterMode_pb2
from model import Filter


class State(Enum):
    STOP = 1
    PLAY = 2
    PAUSE = 3


class CueState:
    def __init__(self, filter_: Filter) -> None:
        self._filter = filter_
        self._state = State.STOP
        self._end_time = datetime.timedelta(seconds=float(20))
        self._paused_time = datetime.timedelta(seconds=float(0))
        self._active_cue = 0
        self._time_scale = 1
        self._start_time = datetime.datetime.now(tz=get_localzone())

    @property
    def playing_cue(self) -> int:
        """Returns the number of the playing cue or -1 if there is none."""
        return self._active_cue if self._state == State.PLAY else -1

    def __str__(self) -> str:
        ret = ""
        if self._state == State.STOP:
            return "stopped"

        if self._state == State.PAUSE:
            ret = "paused at " + self.time_delta_to_str(self._paused_time)
        if self._state == State.PLAY:
            ret = self.time_delta_to_str(
                (datetime.datetime.now(tz=get_localzone()) - self._start_time) * self._time_scale
            )
        return ret + " / " + self.time_delta_to_str(self._end_time) + " in cue " + str(self._active_cue)

    def update(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        values = param.parameter_value.split(";")
        self._start_time = datetime.datetime.now(tz=get_localzone()) - datetime.timedelta(seconds=float(values[2]))
        self._end_time = datetime.timedelta(seconds=float(values[3]))
        self._active_cue = int(values[1])
        self._time_scale = float(values[4])
        if values[0] == "play":
            self._state = State.PLAY
        elif values[0] == "pause":
            self._paused_time = datetime.timedelta(seconds=float(values[2]))
            self._state = State.PAUSE
        elif values[0] == "stop":
            self._state = State.STOP

    def time_delta_to_str(self, delta: datetime.timedelta) -> str:
        ret = ""
        if self._end_time >= datetime.timedelta(days=1):
            days = int(delta.total_seconds() / 86400)
            ret += f"{days:01d}" + "d "
            delta -= datetime.timedelta(days=days)
        if self._end_time >= datetime.timedelta(hours=1):
            hours = int(delta.total_seconds() / 3600)
            ret += f"{hours:02d}" + ":"
            delta -= datetime.timedelta(hours=hours)
        # if self._end_time >= datetime.timedelta(minutes=1):
        minutes = int(delta.total_seconds() / 60)
        ret += f"{minutes:02d}"
        delta -= datetime.timedelta(minutes=minutes)
        if self._end_time < datetime.timedelta(days=1):
            seconds = int(delta.total_seconds())
            ret += ":" + f"{seconds:02d}"
            delta -= datetime.timedelta(seconds=seconds)
        if self._end_time < datetime.timedelta(hours=1):
            ret += "." + f"{int(delta.total_seconds() * 100):02d}"
        return ret
