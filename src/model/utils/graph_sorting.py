"""Provides implementation of the ELK layered layout algorithm to sort filter graphs."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
        port_array = [
            {"id": f"{_filter.filter_id}:{in_port}", "layoutOptions": {"elk.port.side": "WEST"}}
            for in_port in _filter.in_data_types
        ]
        port_array.extend(
            [
                {"id": f"{_filter.filter_id}:{out_port}", "layoutOptions": {"elk.port.side": "EAST"}}
                for out_port in _filter.out_data_types
            ]
        )
        node = {
            "id": _filter.filter_id,
            "width": max(min(250, len(_filter.filter_id) * 10), 80),
            "height": 30 * max(len(_filter.in_data_types.keys()), len(_filter.out_data_types.keys())) + 30,
            "layoutOptions": {"elk.portConstraints": "FIXED_SIDE"},
            "x": _filter.pos[0] if _filter.pos is not None else 0,
            "y": _filter.pos[1] if _filter.pos is not None else 0,
            "ports": port_array,
        }
        child_array.append(node)
        for input_port, connected_output in _filter.channel_links.items():
            edge_array.append(
                {
                    "id": f"e{edge_counter}",
                    "sources": [connected_output],
                    "targets": [f"{_filter.filter_id}:{input_port}"],
                }
            )
            edge_counter += 1
    graph = {
        "id": "root",
        "layoutOptions": {
            "elk.algorithm": "layered",
            "elk.direction": "RIGHT",
        },
        "children": child_array,
        "edges": edge_array,
    }
    result = elk.layout(graph)["children"]
    new_positions = {result_node["id"]: (result_node["x"], result_node["y"]) for result_node in result}
    missing_ids = [_filter.filter_id for _filter in filter_list if _filter.filter_id not in new_positions]
    if missing_ids:
        raise ValueError(f"Expected results with the ids {missing_ids} to exist.")
    for _filter in filter_list:
        _filter.pos = new_positions[_filter.filter_id]
