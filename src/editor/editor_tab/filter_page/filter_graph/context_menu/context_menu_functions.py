"""Functions for the context menu of the nodeditor"""


def delete_nodes_and_pipes(graph):
    """Delete selected nodes and connections."""
    graph.delete_nodes(graph.selected_nodes())
    for pipe in graph.selected_pipes():
        pipe[0].disconnect_from(pipe[1])


def toggle_node_search(graph):
    """Show/hide the node search widget."""
    graph.toggle_node_search()


def expand_group_node(graph):
    """Expand the selected group node."""
    selected_nodes = graph.selected_nodes()
    if not selected_nodes:
        graph.message_dialog('Please select a "GroupNode" to expand.')
        return
    graph.expand_group_node(selected_nodes[0])
