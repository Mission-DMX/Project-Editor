"""logging formatter to json"""
import datetime as dt
import json
from logging import Formatter, LogRecord
from typing import override
from zoneinfo import ZoneInfo

LOG_RECORD_BUILTIN_ATTRS = {"args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName", "levelname",
                            "levelno", "lineno", "module", "msecs", "message", "msg", "name", "pathname", "process",
                            "processName", "relativeCreated", "stack_info", "thread", "threadName", "taskName"}


class JSONFormatter(Formatter):
    """formatter for logging in json """

    def __init__(self, *, fmt_keys: dict[str, str] | None = None) -> None:
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: LogRecord) -> dict[str, str | None]:
        always_fields = {"message": record.getMessage(),
                         "timestamp": dt.datetime.fromtimestamp(record.created,
                                                                tz=ZoneInfo("Europe/Berlin")).isoformat()}
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {key: msg_val if (msg_val := always_fields.pop(val, None)) is not None else getattr(record, val) for
                   key, val in self.fmt_keys.items()}
        message.update(always_fields)

        message.update({key: val for key, val in record.__dict__.items() if key not in LOG_RECORD_BUILTIN_ATTRS})

        return message
