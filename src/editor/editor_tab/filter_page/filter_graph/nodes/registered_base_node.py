from abc import ABC

from bidict import bidict
from NodeGraphQt import BaseNode


class RegisteredBaseNode(BaseNode, ABC):
    _Filter_Types: bidict[str, str] = bidict()
    __representation__ = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__representation__ is not None:
            cls._Filter_Types.update({cls.type_: cls.__representation__})

    def __init__(self):
        super().__init__()

    @classmethod
    def get_filter_type(cls, filter_type: str) -> str:
        """Get a filter type."""
        return cls._Filter_Types.inverse[filter_type]

    @classmethod
    def get_filter_representation(cls, filter_type: str) -> str:
        """Get filter representation."""
        return cls._Filter_Types[filter_type]
