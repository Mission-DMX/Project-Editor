"""Time nodes for the Node Editor."""
from NodeGraphQt import NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import BIT_16_PORT, BIT_8_PORT, DOUBLE_PORT
from editor.editor_tab.filter_page.filter_graph.nodes.registered_base_node import RegisteredBaseNode


def register_time_nodes(graph: NodeGraph) -> None:
    """
    Register all constant nodes in a node graph.
    Args:
        graph: the node graph to register the nodes in.

    """
    graph.register_node(TimeNode)
    graph.register_node(EventCounterNode)
    graph.register_node(TimeSwitchOnDelayBit8Node)
    graph.register_node(TimeSwitchOnDelayBit16Node)
    graph.register_node(TimeSwitchOnDelayFloatNode)
    graph.register_node(TimeSwitchOffDelay8BitNode)
    graph.register_node(TimeSwitchOffDelay16BitNode)
    graph.register_node(TimeSwitchOffDelayFloatNode)


class TimeNode(RegisteredBaseNode):
    """Filter to represent time."""
    NODE_NAME = "Time"
    __identifier__ = "time"
    __representation__ = 32

    def __init__(self) -> None:
        super().__init__()
        self.add_output("value", data_type=DOUBLE_PORT)


class EventCounterNode(RegisteredBaseNode):
    """Filter to count events."""
    NODE_NAME = "Event Counter"
    __identifier__ = "time"
    __representation__ = 70

    def __init__(self) -> None:
        super().__init__()
        self.add_input("time", data_type=DOUBLE_PORT)
        self.add_output("bpm", data_type=BIT_16_PORT)
        self.add_output("freq", data_type=BIT_16_PORT)


class TimeSwitchOnDelayBit8Node(RegisteredBaseNode):
    """Filter to represent an 8-bit - time on-switch."""
    NODE_NAME = "Switch On Delay 8-Bit"
    __identifier__ = "time"
    __representation__ = 33

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=BIT_8_PORT)
        self.add_input("time", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=BIT_8_PORT)


class TimeSwitchOnDelayBit16Node(RegisteredBaseNode):
    """Filter to represent a 16-bit-time on-switch."""
    NODE_NAME = "Switch On Delay 16-Bit"
    __identifier__ = "time"
    __representation__ = 34

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=BIT_16_PORT)
        self.add_input("time", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=BIT_16_PORT)


class TimeSwitchOnDelayFloatNode(RegisteredBaseNode):
    """Filter to represent a float-time on-switch."""
    NODE_NAME = "Switch On Delay Float"
    __identifier__ = "time"
    __representation__ = 35

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_input("time", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class TimeSwitchOffDelay8BitNode(RegisteredBaseNode):
    """Filter to represent an 8-bit - time off-switch."""
    NODE_NAME = "Switch Off Delay 8-Bit"
    __identifier__ = "time"
    __representation__ = 36

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=BIT_8_PORT)
        self.add_input("time", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=BIT_8_PORT)


class TimeSwitchOffDelay16BitNode(RegisteredBaseNode):
    """Filter to represent a 16-bit-time off-switch."""
    NODE_NAME = "Switch Off Delay 16-Bit"
    __identifier__ = "time"
    __representation__ = 37

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=BIT_16_PORT)
        self.add_input("time", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=BIT_16_PORT)


class TimeSwitchOffDelayFloatNode(RegisteredBaseNode):
    """Filter to represent a float-time off-switch."""
    NODE_NAME = "Switch Off Delay Float"
    __identifier__ = "time"
    __representation__ = 38

    def __init__(self):
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_input("time", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)
