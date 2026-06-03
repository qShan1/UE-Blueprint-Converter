from .base import BaseFormatter
from ..transformer.models import TransformedGraph, TransformedNode


class PlainFormatter(BaseFormatter):
    def format(self, graph: TransformedGraph, include_stats: bool = False) -> str:
        lines = []

        for entry in graph.entry_points:
            lines.extend(self._format_node_tree(entry, 0))

        if graph.data_flows:
            lines.append("")
            lines.append("--- Data Flow ---")
            for df in graph.data_flows:
                type_info = f" ({df.data_type})" if df.data_type else ""
                lines.append(
                    f"  {df.target_node}.{df.target_pin} \u2190 {df.source_node}.{df.source_pin}{type_info}"
                )

        if include_stats and graph.stats:
            lines.append("")
            lines.append("--- Statistics ---")
            stats = graph.stats
            lines.append(f"  Total Nodes: {stats.get('total_nodes', 0)}")
            node_type_counts = stats.get("node_type_counts", {})
            if node_type_counts:
                lines.append("  Node Type Counts:")
                for nt, count in sorted(node_type_counts.items()):
                    lines.append(f"    {nt}: {count}")
            lines.append(f"  Variable Reads: {stats.get('variable_reads', 0)}")
            lines.append(f"  Variable Writes: {stats.get('variable_writes', 0)}")
            lines.append(f"  Function Calls: {stats.get('function_calls', 0)}")
            lines.append(f"  Control Flow Nodes: {stats.get('control_flow_nodes', 0)}")

        return "\n".join(lines)

    def _format_node_tree(self, node: TransformedNode, depth: int) -> list[str]:
        lines = []
        indent = "  " * depth

        pin_info = self._format_data_pins(node)
        line = f"{indent}[{node.label}]"
        if pin_info:
            line += f"  ({pin_info})"
        lines.append(line)

        children = node.exec_children
        if not children:
            return lines

        exec_out_pins = [
            p for p in node.pins
            if p.direction == "Output" and p.pin_type == "exec"
        ]

        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            child_indent = "  " * (depth + 1)

            if len(children) == 1:
                connector = "\u2192 "
                pin_label = ""
            else:
                connector = "\u2514\u2500 " if is_last else "\u251c\u2500 "
                pin_label = ""
                if i < len(exec_out_pins):
                    raw = exec_out_pins[i].name
                    pin_label = raw[0].upper() + raw[1:] + " \u2192 "

            child_lines = self._format_node_tree(child, depth + 1)
            child_header = child_lines[0].lstrip()
            child_lines[0] = f"{child_indent}{connector}{pin_label}{child_header}"

            lines.extend(child_lines)

        return lines

    def _format_data_pins(self, node: TransformedNode) -> str:
        data_pins = [
            p for p in node.pins
            if p.direction == "Input" and p.pin_type != "exec"
        ]
        if not data_pins:
            return ""
        parts = []
        for p in data_pins:
            if p.pin_type:
                parts.append(f"{p.name}: {p.pin_type}")
            else:
                parts.append(p.name)
        return ", ".join(parts)