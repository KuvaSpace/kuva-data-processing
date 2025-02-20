"""Functions to serialize custom types to something JSON compatible"""

import json
from typing import Any

import networkx as nx
import numpy as np
from networkx.readwrite import json_graph
from pint import Quantity
from quaternion import quaternion
from rasterio.rpc import RPC

from .custom_types import CRSGeometry


class _NumpyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        return json.JSONEncoder.default(self, o)


def serialize_quaternion(q: quaternion) -> tuple[float, float, float, float]:
    """Serialize quaternion"""
    return (q.w, q.x, q.y, q.z)


def serialize_quantity(q: Quantity) -> tuple[float, str]:
    """Serialize a Pint quantity"""
    return (q.magnitude, str(q.units))


def serialize_ndarray(q: np.ndarray | None) -> list | None:
    """Serialize numpy arrays"""
    return q.tolist() if q is not None else None


def serialize_RPCs(rpcs: RPC | None) -> dict | None:
    """Serialize RPCs"""
    return rpcs.to_dict() if rpcs is not None else None


def serialize_CRSGeometry(p: CRSGeometry) -> dict[str, Any]:
    """Serialize geometries with associated CRS"""
    return {"geom": p.geom.wkt, "crs_epsg": p.crs_epsg.to_epsg()}


def serialize_graph(g: nx.DiGraph | None, context: dict[str, Any]) -> str | None:
    """Serialize Networkkx Graph with numpy arrays."""
    if g is None:
        return None
    out = json.dumps(json_graph.adjacency_data(g), cls=_NumpyEncoder, indent=2)

    image_path = context["image_path"]
    graph_json_file_name = context["graph_json_file_name"]

    with (image_path / graph_json_file_name).open('w') as fh:
        fh.write(out)

    return graph_json_file_name
