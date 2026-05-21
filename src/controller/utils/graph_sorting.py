"""Provides implementation of Fruchterman-Reingold algorithm to sort graphs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pyelk import ELK

if TYPE_CHECKING:
    from model import Filter


def layered_layout(filter_list: list[Filter]) -> None:
    """Sort provided _filter list using Sugiyama algorithm.

    This method modifies the positions of the provided filters in place.

    Args:
        filter_list: List of filters to sort.

    """
    elk = ELK()
    child_array = []
    edge_array = []
    edge_counter = 0
    for _filter in filter_list:
        port_array = [{
            "id": f"{_filter.filter_id}:{in_port}",
            "layoutOptions": {"elk.port.side": "EAST"}
        } for in_port in _filter.in_data_types]
        port_array.extend([{
            "id": f"{_filter.filter_id}:{out_port}",
            "layoutOptions": {"elk.port.side": "WEST"}
        } for out_port in _filter.out_data_types])
        node = {
            "id": _filter.filter_id,
            "width": max(min(250, len(_filter.filter_id) * 10), 80),
            "height": 30 * max(len(_filter.in_data_types.keys()), len(_filter.out_data_types.keys())) + 30,
            "layoutOptions": {"elk.portConstraints": "FIXED_SIDE"},
            "x": _filter.pos[0],
            "y": _filter.pos[1],
            "ports": port_array,
        }
        child_array.append(node)
        for input_port, connected_output in _filter.channel_links.items():
            edge_array.append({
                "id": f"e{edge_counter}",
                "sources": [connected_output],
                "targets": [f"{_filter.filter_id}:{input_port}"],
            })
            edge_counter += 1
    graph = {
        "id": "root",
        "layoutOptions": {
            "elk.algorithm": "layered",
            "elk.direction": "RIGHT",
        },
        "children": child_array,
        "edges": edge_array
    }
    result = elk.layout(graph)["children"]
    for _filter in filter_list:
        result_node = None
        for r in result:
            if r["id"] == _filter.filter_id:
                result_node = r
                break
        if result_node is None:
            raise ValueError(f"Expected a result with id {_filter.filter_id} to exist.")
        _filter.pos = (result_node["x"], result_node["y"])


def spring_layout(
    filter_list: list[Filter],
    k: float | None = None,
    iterations: int = 50,
    threshold: int =1e-4
) -> np.ndarray:
    """Position nodes using Fruchterman-Reingold force-directed algorithm.

    This method modifies the positions of the provided filters in place.

    The algorithm simulates a force-directed representation of the network
    treating edges as springs holding nodes close, while treating nodes
    as repelling objects, sometimes called an anti-gravity force.
    Simulation continues until the positions are close to an equilibrium.

    There are some hard-coded values: minimal distance between
    nodes (0.01) and "temperature" of 0.1 to ensure nodes don't fly away.
    During the simulation, `k` helps determine the distance between nodes,
    though `scale` and `center` determine the size and place after
    rescaling occurs at the end of the simulation.

    Args:
        filter_list : list of filters
            matrix_a position will be assigned to every node in G.

        k: default=None
            Optimal distance between nodes.  If None the distance is set to
            1/sqrt(node) where node is the number of nodes.  Increase this value
            to move nodes farther apart.

        iterations: optional (default=50)
            Maximum number of iterations taken

        threshold: optional (default = 1e-4)
            Threshold for relative error in node position changes.
            The iteration stops if the error is below this threshold.

    """
    dim = 2
    scale = 250
    if len(filter_list) == 0:
        return None

    center = np.zeros(dim)

    # Determine size of existing domain to adjust initial positions
    dom_size = max(max(f.pos[0], f.pos[1]) for f in filter_list)
    if dom_size == 0:
        dom_size = 1

    # Load initial positions from nodes
    pos_arr = np.ones((len(filter_list), dim)) * dom_size + center
    for i, node in enumerate(filter_list):
        pos_arr[i] = np.asarray(node.pos)

    # Sparse matrix
    matrix_a = _generate_graph_matrix_from_filters(filter_list) # convert graph to matrix

    # calculate positions
    pos = _fruchterman_reingold(
        matrix_a, k, pos_arr, None, iterations, threshold, dim, None
    )

    pos = _rescale_layout(pos, scale=scale) + center
    # FIXME we need to move all following connected nodes as input port != output port
    # FIXME successor nodes should be placed behind prior nodes
    # Maybe Eclipse Layout Kernel Layered would help here?
    for node, new_pos in zip(filter_list, pos, strict=True):
        node.pos = new_pos

    return pos

def _generate_graph_matrix_from_filters(filters: list[Filter]) -> np.ndarray:
    arr = np.zeros((len(filters), len(filters)))
    index_dict = {f: i for i, f in enumerate(filters)}
    name_dict = {f.filter_id: f for f in filters}
    for node in filters:
        own_index = index_dict[node]
        for incomming_edge in node.channel_links.values():
            foreign_filter_id, _ = incomming_edge.split(":")
            if foreign_filter_id in name_dict:
                foreign_filter_index = index_dict[name_dict[foreign_filter_id]]
                arr[foreign_filter_index][own_index] = 1
    return arr


def _fruchterman_reingold(
    martix_a: np.ndarray,
    k: float | None = None,
    pos: np.ndarray | None = None,
    fixed: np.ndarray | None = None,
    iterations: int = 50,
    threshold: int = 1e-4,
    dim: int = 2, seed: np.random.seed | None = None
) -> None:
    # Position nodes in adjacency matrix A using Fruchterman-Reingold
    # Entry point for NetworkX graph is fruchterman_reingold_layout()

    try:
        nnodes, _ = martix_a.shape
    except AttributeError as err:
        raise ValueError("fruchterman_reingold() takes an adjacency matrix as input") from err

    pos = np.asarray(seed.rand(nnodes, dim), dtype=martix_a.dtype) if pos is None else pos.astype(martix_a.dtype)

    # optimal distance between nodes
    if k is None:
        k = np.sqrt(1.0 / nnodes)
    # the initial "temperature"  is about .1 of domain area (=1x1)
    # this is the largest step allowed in the dynamics.
    # We need to calculate this in case our fixed positions force our domain
    # to be much bigger than 1x1
    t = max(max(pos.T[0]) - min(pos.T[0]), max(pos.T[1]) - min(pos.T[1])) * 0.1
    # simple cooling scheme.
    # linearly step down by dt on each iteration so last iteration is size dt.
    dt = t / (iterations + 1)
    delta = np.zeros((pos.shape[0], pos.shape[0], pos.shape[1]), dtype=martix_a.dtype)
    # the inscrutable (but fast) version
    # this is still O(V^2)
    # could use multilevel methods to speed this up significantly
    for _ in range(iterations):
        # matrix of difference between points
        delta = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
        # distance between points
        distance = np.linalg.norm(delta, axis=-1)
        # enforce minimum distance of 0.01
        np.clip(distance, 0.01, None, out=distance)
        # displacement "force"
        displacement = np.einsum(
            "ijk,ij->ik", delta, (k * k / distance ** 2 - martix_a * distance / k)
        )
        # update positions
        length = np.linalg.norm(displacement, axis=-1)
        # Threshold the minimum length prior to position scaling
        # See gh-8113 for detailed discussion of the threshold
        length = np.clip(length, a_min=0.01, a_max=None)
        delta_pos = np.einsum("ij,i->ij", displacement, t / length)
        if fixed is not None:
            # don't change positions of fixed nodes
            delta_pos[fixed] = 0.0
        pos += delta_pos
        # cool temperature
        t -= dt
        if (np.linalg.norm(delta_pos) / nnodes) < threshold:
            break
    return pos

def _rescale_layout(pos: np.ndarray, scale: float = 100) -> np.ndarray:
    """Returns scaled position array to (-scale, scale) in all axes."""
    # Find max length over all dimensions
    pos -= pos.mean(axis=0)
    lim = np.abs(pos).max()  # max coordinate for all axes
    # rescale to (-scale, scale) in all directions, preserves aspect
    if lim > 0:
        pos *= scale / lim
    return pos
