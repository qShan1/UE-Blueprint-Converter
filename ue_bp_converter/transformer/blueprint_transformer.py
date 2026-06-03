import re

from .models import TransformedGraph, TransformedNode, DataFlowEdge
from ..parser.models import BlueprintGraph


LABEL_MAP = {
    "EventBeginPlay": "On Begin Play",
    "EventTick": "On Tick",
    "Branch": "If/Else Branch",
    "ForLoop": "For Loop",
    "ForEachLoop": "For Each Loop",
    "ExecutionSequence": "Sequence",
    "DynamicCast": "Cast To",
    "Select": "Select (Ternary)",
    "Switch": "Switch",
    "MathExpression": "Math Expression",
    "BinaryOperator": "Math Operation",
}


METADATA_CLEAN_PATTERNS = [
    re.compile(r"^bIs"),
    re.compile(r"^NodePos"),
    re.compile(r"^NodeGuid$"),
    re.compile(r"Guid$"),
    re.compile(r"^CachedNodeTitle$"),
    re.compile(r"PinType"),
]


class BlueprintTransformer:
    def __init__(self) -> None:
        pass

    def transform(self, graph: BlueprintGraph) -> TransformedGraph:
        self._clean_metadata(graph)

        name_to_node = {n.name: n for n in graph.nodes}

        children_of = self._build_exec_adjacency(graph)
        entry_names = self._find_entry_points(graph)
        name_to_id = {}
        all_nodes: dict[str, TransformedNode] = {}
        id_counter = [0]

        def build_transformed(name: str) -> str:
            if name in name_to_id:
                return name_to_id[name]
            node_info = name_to_node[name]
            label = self._map_label(node_info.node_type)
            node_id = f"node_{id_counter[0]}"
            id_counter[0] += 1
            name_to_id[name] = node_id

            tnode = TransformedNode(
                id=node_id,
                label=label,
                node_type=node_info.node_type,
                pins=node_info.pins,
                variables=node_info.variables,
                exec_children=[],
            )
            all_nodes[node_id] = tnode

            child_names = [tgt for tgt, _ in children_of.get(name, [])]
            for child_name in child_names:
                if child_name in name_to_node and child_name not in name_to_id:
                    child_id = build_transformed(child_name)
                    child_node = all_nodes[child_id]
                    tnode.exec_children.append(child_node)

            return node_id

        entry_nodes = []
        for name in entry_names:
            if name in name_to_node:
                build_transformed(name)
                entry_nodes.append(all_nodes[name_to_id[name]])

        for node in graph.nodes:
            if node.name not in name_to_id:
                label = self._map_label(node.node_type)
                node_id = f"node_{id_counter[0]}"
                id_counter[0] += 1
                name_to_id[node.name] = node_id
                tnode = TransformedNode(
                    id=node_id,
                    label=label,
                    node_type=node.node_type,
                    pins=node.pins,
                    variables=node.variables,
                    exec_children=[],
                )
                all_nodes[node_id] = tnode

        data_flows = self._build_data_flows(graph, name_to_id, name_to_node)
        stats = self._generate_stats(graph)

        return TransformedGraph(
            entry_points=entry_nodes,
            all_nodes=all_nodes,
            data_flows=data_flows,
            stats=stats,
        )

    def _clean_metadata(self, graph: BlueprintGraph) -> None:
        for node in graph.nodes:
            keys_to_remove = []
            for key in node.metadata:
                for pattern in METADATA_CLEAN_PATTERNS:
                    if pattern.search(key):
                        keys_to_remove.append(key)
                        break
            for key in keys_to_remove:
                del node.metadata[key]

    def _map_label(self, node_type: str) -> str:
        if node_type in LABEL_MAP:
            return LABEL_MAP[node_type]

        if node_type.startswith("InputAction"):
            return node_type

        if node_type.endswith(" (Get)") or node_type.endswith(" (Set)"):
            return node_type

        if "Unknown" in node_type:
            return f"[Unknown] {node_type}"

        if node_type == "CallFunction":
            return node_type

        return node_type

    def _build_exec_adjacency(
        self, graph: BlueprintGraph
    ) -> dict[str, list[tuple[str, int]]]:
        children_of: dict[str, list[tuple[str, int]]] = {}
        for src, tgt, order in graph.exec_flow:
            if src not in children_of:
                children_of[src] = []
            children_of[src].append((tgt, order))
        for src in children_of:
            children_of[src].sort(key=lambda x: x[1])
        return children_of

    def _find_entry_points(self, graph: BlueprintGraph) -> list[str]:
        all_sources = {src for src, _, _ in graph.exec_flow}
        all_targets = {tgt for _, tgt, _ in graph.exec_flow}
        entry_names = [n.name for n in graph.nodes if n.name in all_sources and n.name not in all_targets]
        return entry_names

    def _build_data_flows(
        self,
        graph: BlueprintGraph,
        name_to_id: dict[str, str],
        name_to_node: dict[str, "NodeInfo"],
    ) -> list[DataFlowEdge]:
        data_flows = []
        for src_name, src_pin, tgt_name, tgt_pin in graph.data_flow:
            if src_name in name_to_id and tgt_name in name_to_id:
                data_type = ""
                if src_name in name_to_node:
                    for pin in name_to_node[src_name].pins:
                        if pin.name == src_pin:
                            data_type = pin.pin_type
                            break
                data_flows.append(
                    DataFlowEdge(
                        source_node=name_to_id[src_name],
                        source_pin=src_pin,
                        target_node=name_to_id[tgt_name],
                        target_pin=tgt_pin,
                        data_type=data_type,
                    )
                )
        return data_flows

    def _generate_stats(self, graph: BlueprintGraph) -> dict:
        stats: dict = {
            "total_nodes": len(graph.nodes),
            "node_type_counts": {},
            "variable_reads": 0,
            "variable_writes": 0,
            "function_calls": 0,
            "control_flow_nodes": 0,
        }

        control_flow_types = {"Branch", "ForLoop", "ForEachLoop", "Switch", "Select"}

        for node in graph.nodes:
            nt = node.node_type
            stats["node_type_counts"][nt] = stats["node_type_counts"].get(nt, 0) + 1

            for var in node.variables:
                if var.operation == "read":
                    stats["variable_reads"] += 1
                elif var.operation == "write":
                    stats["variable_writes"] += 1

            if nt in control_flow_types:
                stats["control_flow_nodes"] += 1

            if "K2Node_CallFunction" in node.raw_type:
                stats["function_calls"] += 1

        return stats