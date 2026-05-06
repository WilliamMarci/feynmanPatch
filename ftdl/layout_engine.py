# feynmanPatch/ftdl/layout_engine.py

from collections import deque


class LayoutEngine(object):

    def __init__(self, graph):
        self.graph = graph

    def compute(self):
        nodes = self.graph.nodes
        edges = self.graph.edges
        if not nodes:
            return

        external = [n for n in nodes if n["external"]]
        internal = [n for n in nodes if not n["external"]]

        left_ids, right_ids = self._classify_external_sides(edges, external)
        left_nodes = [n for n in external if n["id"] in left_ids]
        right_nodes = [n for n in external if n["id"] in right_ids]

        self._place_external_evenly(left_nodes, 0.0)
        self._place_external_evenly(right_nodes, 1.0)

        if not internal:
            return

        self._assign_levels(internal, edges, left_ids)
        max_lv = max((n.get("_level", 0) for n in internal), default=0)
        max_lv = max(max_lv, 0)

        self._place_internal_levels(internal, max_lv)

        self._pull_toward_connections(internal, edges, left_nodes, right_nodes)

    def _classify_external_sides(self, edges, external):
        left_ids = set()
        right_ids = set()
        ext_ids = set(n["id"] for n in external)

        for e in edges:
            f_ext = e["from"] in ext_ids
            t_ext = e["to"] in ext_ids
            if f_ext and not t_ext:
                left_ids.add(e["from"])
            elif t_ext and not f_ext:
                right_ids.add(e["to"])

        remaining = ext_ids - left_ids - right_ids
        for rid in remaining:
            right_ids.add(rid)

        return left_ids, right_ids

    def _place_external_evenly(self, ext_nodes, x_target):
        n = len(ext_nodes)
        if n == 0:
            return
        margin = 0.08
        if n == 1:
            ext_nodes[0]["x"] = x_target
            ext_nodes[0]["y"] = 0.5
        else:
            span = 1.0 - 2 * margin
            step = span / (n - 1)
            for i, node in enumerate(ext_nodes):
                node["x"] = x_target
                node["y"] = round(margin + i * step, 4)

    def _assign_levels(self, internal, edges, left_ids):
        adj = {n["id"]: [] for n in internal}
        int_ids = set(n["id"] for n in internal)

        for e in edges:
            f = e["from"]
            t = e["to"]
            if f in int_ids and t in int_ids:
                adj[f].append(t)
                adj[t].append(f)

        for n in internal:
            n["_level"] = 999

        queue = deque()
        for n in internal:
            for e in edges:
                if e["from"] == n["id"] and e["to"] in left_ids:
                    n["_level"] = 0
                    queue.append(n["id"])
                    break
                if e["to"] == n["id"] and e["from"] in left_ids:
                    n["_level"] = 0
                    queue.append(n["id"])
                    break

        self._bfs_levels(internal, adj, queue)

        min_lv = min((n["_level"] for n in internal if n["_level"] < 999), default=0)
        for n in internal:
            if n["_level"] < 999:
                n["_level"] -= min_lv

    def _bfs_levels(self, internal, adj, queue):
        while queue:
            cur_id = queue.popleft()
            cur = self._by_id(cur_id)
            if not cur:
                continue
            clv = cur.get("_level", 0)
            for nb_id in adj.get(cur_id, []):
                nb = self._by_id(nb_id)
                if nb and nb["_level"] > clv + 1:
                    nb["_level"] = clv + 1
                    queue.append(nb_id)

    def _place_internal_levels(self, internal, max_lv):
        level_groups = {}
        for n in internal:
            lv = n.get("_level", 0)
            level_groups.setdefault(lv, []).append(n)

        max_per_level = max((len(g) for g in level_groups.values()), default=1)

        x_margin = 0.18
        x_span = 1.0 - 2 * x_margin

        if max_lv == 0:
            nint = len(internal)
            if nint == 1:
                internal[0]["x"] = 0.5
                internal[0]["y"] = 0.5
            else:
                for i, n in enumerate(internal):
                    n["x"] = round(x_margin + x_span * i / (nint - 1), 4) if nint > 1 else 0.5
                    n["y"] = 0.5
            return

        y_margin = 0.12
        y_span = 1.0 - 2 * y_margin
        slot_step = y_span / max(max_per_level - 1, 1)

        for lv, group in level_groups.items():
            x = round(x_margin + x_span * lv / max_lv, 4)
            ng = len(group)
            for i, n in enumerate(group):
                n["x"] = x
                if ng == 1:
                    n["y"] = 0.5
                else:
                    total_width = (ng - 1) * slot_step
                    y_start = 0.5 - total_width / 2.0
                    n["y"] = round(y_start + i * slot_step, 4)

    def _pull_toward_connections(self, internal, edges, left_nodes, right_nodes):
        for n in internal:
            conn_y = []
            for e in edges:
                if e["from"] == n["id"]:
                    tgt = self._by_id(e["to"])
                    if tgt and tgt["external"]:
                        conn_y.append(tgt["y"])
                if e["to"] == n["id"]:
                    tgt = self._by_id(e["from"])
                    if tgt and tgt["external"]:
                        conn_y.append(tgt["y"])
            if conn_y:
                n["y"] = round(sum(conn_y) / len(conn_y), 4)

    def _by_id(self, nid):
        for n in self.graph.nodes:
            if n["id"] == nid:
                return n
        return None
