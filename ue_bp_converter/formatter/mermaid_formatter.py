from .base import BaseFormatter
from ..transformer.models import TransformedGraph, TransformedNode


class MermaidFormatter(BaseFormatter):
    def format(self, graph: TransformedGraph, include_stats: bool = False) -> str:
        lines = []
        lines.append("```mermaid")
        lines.append("flowchart TD")
        lines.append("")

        sorted_ids = sorted(graph.all_nodes.keys(), key=lambda x: int(x.split("_")[1]))
        for nid in sorted_ids:
            node = graph.all_nodes[nid]
            escaped_label = node.label.replace('"', "#quot;")
            lines.append(f'    {nid}["{escaped_label}"]')

        lines.append("")

        exec_edges = self._collect_exec_edges(graph)
        for src_id, tgt_id, label in exec_edges:
            if label:
                escaped_label = label.replace('"', "#quot;")
                lines.append(f'    {src_id} -->|"{escaped_label}"| {tgt_id}')
            else:
                lines.append(f"    {src_id} --> {tgt_id}")

        if graph.data_flows:
            lines.append("")
            for df in graph.data_flows:
                escaped_label = df.source_pin.replace('"', "#quot;")
                lines.append(
                    f'    {df.source_node} -.->|"{escaped_label}"| {df.target_node}'
                )

        if include_stats and graph.stats:
            stats = graph.stats
            lines.append("")
            lines.append(f"    %% Total Nodes: {stats.get('total_nodes', 0)}")
            lines.append(f"    %% Variable Reads: {stats.get('variable_reads', 0)}")
            lines.append(f"    %% Variable Writes: {stats.get('variable_writes', 0)}")
            lines.append(f"    %% Function Calls: {stats.get('function_calls', 0)}")
            lines.append(f"    %% Control Flow Nodes: {stats.get('control_flow_nodes', 0)}")

        lines.append("```")
        return "\n".join(lines) + "\n"

    def _collect_exec_edges(self, graph: TransformedGraph) -> list[tuple[str, str, str]]:
        edges = []

        def walk(node: TransformedNode) -> None:
            exec_out_pins = [
                p for p in node.pins
                if p.direction == "Output" and p.pin_type == "exec"
            ]
            for i, child in enumerate(node.exec_children):
                label = ""
                if i < len(exec_out_pins):
                    raw = exec_out_pins[i].name
                    label = raw[0].upper() + raw[1:]
                edges.append((node.id, child.id, label))
                walk(child)

        for entry in graph.entry_points:
            walk(entry)

        return edges