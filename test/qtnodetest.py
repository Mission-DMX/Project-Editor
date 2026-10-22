from PySide6 import QtWidgets
from NodeGraphQt import NodeGraph, BaseNode



# create a node class object inherited from BaseNode.

class FooNode(BaseNode):


    # unique node identifier domain.

    __identifier__ = 'io.github.jchanvfx'


    # initial default node name.

    NODE_NAME = 'Foo Node'


    def __init__(self):

        super(FooNode, self).__init__()


        # create an input port.

        self.add_input('in', color=(180, 80, 0))


        # create an output port.

        self.add_output('out')



if __name__ == '__main__':

    app = QtWidgets.QApplication([])


    # create node graph controller.

    graph = NodeGraph()


    # register the FooNode node class.

    graph.register_node(FooNode)


    # show the node graph widget.

    graph_widget = graph.widget

    graph_widget.show()


    # create two nodes.

    node_a = graph.create_node('io.github.jchanvfx.FooNode', name='node A')

    node_b = graph.create_node('io.github.jchanvfx.FooNode', name='node B', pos=(300, 50))
    a_nodes = []
    for i in range(500):
        node = graph.create_node('io.github.jchanvfx.FooNode', name='node A{}'.format(i), pos=(100, 50*i))
        a_nodes.append(node)
    for i in range(500):
        node = graph.create_node('io.github.jchanvfx.FooNode', name='node B{}'.format(i), pos=(500, 50*i))
        node.set_input(0, a_nodes[(i + 30) % 500].output(0))


    # connect node_a to node_b

    node_a.set_output(0, node_b.input(0))
    app.exec_()