from abc import ABC, abstractmethod

from model import DataType
from model.control_desk import BankSet, DeskColumn
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget


class ExternalChannelDefinition:
    """In case we're in preview mode we need to instantiate filters for the preview based on this information.

    As I didn't want to write a tuple of the channel name, its type as well as fader source, this class provides them
    in a named fashion.
    """

    def __init__(self, data_type: DataType, name: str, associated_fader: DeskColumn, bank_set: BankSet):
        self.data_type = data_type
        self.name = name
        self.fader = associated_fader
        self.bankset = bank_set
        self.enabled = True


class PreviewEditWidget(NodeEditorFilterConfigWidget, ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_channel_list(self) -> list[ExternalChannelDefinition]:
        """
        This method needs to return the list of exposed channels. It may return a mutable list as it will be
        copied anyway

        :returns: A list of ExternalChannelDefinition objects
        """
        raise NotImplementedError()

    @property
    def channels(self) -> list[ExternalChannelDefinition]:
        return self.get_channel_list().copy()
