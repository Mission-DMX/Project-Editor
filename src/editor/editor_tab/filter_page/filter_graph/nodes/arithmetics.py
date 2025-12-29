"""Constant nodes for the Node Editor."""
from NodeGraphQt import BaseNode, NodeGraph

from editor.editor_tab.filter_page.filter_graph.nodes.ports import BIT_16_PORT, BIT_8_PORT, DOUBLE_PORT


def register_arithmetic_nodes(graph: NodeGraph) -> None:
    """
    Register all arithmetic nodes in a node graph.
    Args:
        graph: graph to register the nodes in
    """
    graph.register_node(MACNode)
    graph.register_node(FloatTo8BitNode)
    graph.register_node(FloatTo16BitNode)
    graph.register_node(RoundNode)
    graph.register_node(LogarithmNode)
    graph.register_node(ExponentialNode)
    graph.register_node(MinimumNode)
    graph.register_node(MaximumNode)
    graph.register_node(SumBit8Node)
    graph.register_node(SumBit16Node)
    graph.register_node(SumFloatNode)


class MACNode(BaseNode):
    """Filter to calculate MAC value.

    value = (factor1 * factor2) + summand.
    """
    NODE_NAME = "MAC Filter"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("factor1", data_type=DOUBLE_PORT)
        self.add_input("factor2", data_type=DOUBLE_PORT)
        self.add_input("summand", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class FloatTo8BitNode(BaseNode):
    """Filter to round a float/double value to an 8-bit value."""
    NODE_NAME = "Float To 8-Bit"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=BIT_8_PORT)


class FloatTo16BitNode(BaseNode):
    """Filter to round a float/double value to an 8-bit value."""
    NODE_NAME = "Float To 16-Bit"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=BIT_16_PORT)


class RoundNode(BaseNode):
    """Filter to round a float/double value to a float/double value."""
    NODE_NAME = "Round"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class LogarithmNode(BaseNode):
    """Filter to calculate a logarithm value.

       value = ln(value_in).

    """
    NODE_NAME = "log"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class ExponentialNode(BaseNode):
    """Filter to calculate an exponential value.

        value = exp(value_in)

    """
    NODE_NAME = "exp"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("value_in", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class MinimumNode(BaseNode):
    """Filter to calculate the minimum value.

     value = min(param1, param2)
    """
    NODE_NAME = "min"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("param1", data_type=DOUBLE_PORT)
        self.add_input("param2", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class MaximumNode(BaseNode):
    """Filter to calculate the maximum of two values.

        value = max(param1, param2)
   """
    NODE_NAME = "max"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.add_input("param1", data_type=DOUBLE_PORT)
        self.add_input("param2", data_type=DOUBLE_PORT)
        self.add_output("value", data_type=DOUBLE_PORT)


class SumBit8Node(BaseNode):
    """Filter to calculate the sum of 8-bit values."""
    NODE_NAME = "8-Bit Sum"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.set_port_deletion_allowed(True)
        self.add_button("add", text="+")
        self.add_button("remove", text="-")
        self.widgets()["add"].value_changed.connect(self._add_bit_8_input)
        self.widgets()["remove"].value_changed.connect(self._remove_input)
        self.add_output("value", data_type=BIT_8_PORT)

    def _add_bit_8_input(self) -> None:
        self.add_input("value" + str(len(self.inputs())), data_type=BIT_8_PORT)

    def _remove_input(self) -> None:
        self.delete_input("value" + str(len(self.inputs()) - 1))


class SumBit16Node(BaseNode):
    """Filter to calculate the sum of 16-bit values."""
    NODE_NAME = "16-Bit Sum"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.set_port_deletion_allowed(True)
        self.add_button("add", text="+")
        self.add_button("remove", text="-")
        self.widgets()["add"].value_changed.connect(self._add_bit_16_input)
        self.widgets()["remove"].value_changed.connect(self._remove_input)
        self.add_output("value", data_type=BIT_8_PORT)

    def _add_bit_16_input(self) -> None:
        self.add_input("value" + str(len(self.inputs())), data_type=BIT_16_PORT)

    def _remove_input(self) -> None:
        self.delete_input("value" + str(len(self.inputs()) - 1))


class SumFloatNode(BaseNode):
    """Filter to calculate the sum of float values."""
    NODE_NAME = "Float Sum"
    __identifier__ = "arithmetic"

    def __init__(self) -> None:
        super().__init__()
        self.set_port_deletion_allowed(True)
        self.add_button("add", text="+")
        self.add_button("remove", text="-")
        self.widgets()["add"].value_changed.connect(self._add_bit_16_input)
        self.widgets()["remove"].value_changed.connect(self._remove_input)
        self.add_output("value", data_type=BIT_8_PORT)

    def _add_bit_16_input(self) -> None:
        self.add_input("value" + str(len(self.inputs())), data_type=DOUBLE_PORT)

    def _remove_input(self) -> None:
        self.delete_input("value" + str(len(self.inputs()) - 1))
