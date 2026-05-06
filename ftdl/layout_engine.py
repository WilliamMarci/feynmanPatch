# feynmanPatch/ftdl/layout_engine.py

import math


class LayoutEngine(object):

    def __init__(self, graph):
        self.graph = graph

    def compute(self):
        nodes = self.graph.nodes
        edges = self.graph.edges

        if not nodes:
            return

        internal = [n for n in nodes if not n["external"]]
        external_left = []
        external_right = []
        external_undetermined = []

        for n in nodes:
            if n["external"]:
                n_left = any(e["from"] == n["id"] and e["external"] for e in edges)
                n_right = any(e["to"] == n["id"] and e["external"] for e in edges)
                if n_left and not n_right:
                    external_left.append(n)
                elif n_right and not n_left:
                    external_right.append(n)
                else:
                    external_undetermined.append(n)

        if not external_left and not external_right:
            for e in edges:
                if e["external"]:
                    if e["state"]:
                        external_right.append(self._node_by_id(e["to"]))
                    else:
                        external_left.append(self._node_by_id(e["from"]))

        self._place_external(external_left, 0.0)
        self._place_external(external_right, 1.0)
        self._place_external(external_undetermined, 0.5)

        num_internal = len(internal)
        if num_internal == 0:
            return
        elif num_internal == 1:
            internal[0]["x"] = 0.5
            internal[0]["y"] = 0.5
        elif num_internal == 2:
            internal[0]["x"] = 0.35
            internal[0]["y"] = 0.5
            internal[1]["x"] = 0.65
            internal[1]["y"] = 0.5
        else:
            for i, node in enumerate(internal):
                node["x"] = 0.3 + 0.4 * (i + 1) / (num_internal + 1)
                node["y"] = 0.5

        self._resolve_conflicting_y(internal, external_left, external_right, edges)

    def _node_by_id(self, nid):
        for n in self.graph.nodes:
            if n["id"] == nid:
                return n
        return None

    def _place_external(self, ext_nodes, x_target):
        n_ext = len(ext_nodes)
        if n_ext == 0:
            return
        if n_ext == 1:
            ext_nodes[0]["x"] = x_target
            ext_nodes[0]["y"] = 0.5
        else:
            for i, node in enumerate(ext_nodes):
                node["x"] = x_target
                node["y"] = i / (n_ext - 1) if n_ext > 1 else 0.5
                if node["y"] == 0.0:
                    node["y"] = 0.05
                elif node["y"] == 1.0:
                    node["y"] = 0.95

    def _resolve_conflicting_y(self, internal, left, right, edges):
        for iv in internal:
            connections_left = []
            connections_right = []
            for e in edges:
                if e["to"] == iv["id"] and e["external"]:
                    left_node = self._node_by_id(e["from"])
                    if left_node and left_node["x"] < iv["x"]:
                        connections_left.append(left_node)
                if e["from"] == iv["id"] and e["external"]:
                    right_node = self._node_by_id(e["to"])
                    if right_node and right_node["x"] > iv["x"]:
                        connections_right.append(right_node)

            if connections_left:
                y_avg = sum(n["y"] for n in connections_left) / len(connections_left)
                iv["y"] = y_avg
            elif connections_right:
                y_avg = sum(n["y"] for n in connections_right) / len(connections_right)
                iv["y"] = y_avg
