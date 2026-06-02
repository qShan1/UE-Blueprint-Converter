from .base import BaseFormatter
from ..transformer.models import TransformedGraph, TransformedNode


class MarkdownFormatter(BaseFormatter):
    def format(self, graph: TransformedGraph, include_stats: bool = False) -> str:
        sections = []
        sections.append("# Blueprint Analysis")
        sections.append("")

        sections.append(self._format_node_summary(graph))
        sections.append("")

        sections.append(self._format_execution_flow(graph))
        sections.append("")

        if graph.data_flows:
            sections.append(self._format_data_flow(graph))
            sections.append("")

        if include_stats and graph.stats:
            sections.append(self._format_stats(graph))

        return "\n".join(sections).rstrip() + "\n"

    def _format_node_summary(self, graph: TransformedGraph) -> str:
        lines = ["## Node Summary", ""]
        lines.append("| ID | Label | Type | Pins |")
        lines.append("|---|------|------|------|")

        sorted_ids = sorted(graph.all_nodes.keys(), key=lambda x: int(x.split("_")[1]))
        for nid in sorted_ids:
            node = graph.all_nodes[nid]
            pin_desc = self._describe_pins(node)
            lines.append(f"| {nid} | {node.label} | {node.node_type} | {pin_desc} |")

        return "\n".join(lines)

    def _describe_pins(self, node: TransformedNode) -> str:
        parts = []
        for p in node.pins:
            if p.pin_type == "exec":
                parts.append(f"{p.name}(exec)")
            else:
                type_str = f":{p.pin_type}" if p.pin_type else ""
                parts.append(f"{p.name}({p.direction.lower()}{type_str})")
        return ", ".join(parts)

    def _format_execution_flow(self, graph: TransformedGraph) -> str:
        lines = ["## Execution Flow", ""]
        counter = [1]

        for i, entry in enumerate(graph.entry_points):
            item_lines = self._format_exec_node(entry, 0, counter, i == len(graph.entry_points) - 1)
            lines.extend(item_lines)

        return "\n".join(lines)

    def _format_exec_node(
        self, node: TransformedNode, depth: int, counter: list[int], is_last_sibling: bool
    ) -> list[str]:
        lines = []
        indent = "  " * depth
        exec_out_pins = [
            p for p in node.pins
            if p.direction == "Output" and p.pin_type == "exec"
        ]

        if depth == 0:
            num = counter[0]
            counter[0] += 1
            lines.append(f"{indent}{num}. **{node.label}** ({node.id})")
        else:
            parent_indent = "  " * (depth - 1)
            if len(exec_out_pins) >= depth and depth > 0:
                pass
            lines.append(f"{indent}- \u2192 **{node.label}** ({node.id})")

        for i, child in enumerate(node.exec_children):
            child_lines = self._format_exec_node(child, depth + 1, counter, i == len(node.exec_children) - 1)
            lines.extend(child_lines)

        return lines

    def _format_data_flow(self, graph: TransformedGraph) -> str:
        lines = ["## Data Flow", ""]
        lines.append("| From | Pin | \u2192 | To | Pin | Type |")
        lines.append("|------|-----|---|----|-----|------|")

        for df in graph.data_flows:
            lines.append(
                f"| {df.source_node} | {df.source_pin} | \u2192 "
                f"| {df.target_node} | {df.target_pin} | {df.data_type} |"
            )

        return "\n".join(lines)

    def _format_stats(self, graph: TransformedGraph) -> str:
        lines = ["## Statistics", ""]
        stats = graph.stats
        lines.append(f"- **Total Nodes**: {stats.get('total_nodes', 0)}")
        lines.append(f"- **Variable Reads**: {stats.get('variable_reads', 0)}")
        lines.append(f"- **Variable Writes**: {stats.get('variable_writes', 0)}")
        lines.append(f"- **Function Calls**: {stats.get('function_calls', 0)}")
        lines.append(f"- **Control Flow Nodes**: {stats.get('control_flow_nodes', 0)}")

        node_type_counts = stats.get("node_type_counts", {})
        if node_type_counts:
            lines.append("- **Node Type Counts**:")
            for nt, count in sorted(node_type_counts.items()):
                lines.append(f"  - {nt}: {count}")

        return "\n".join(lines)