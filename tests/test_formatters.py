import pytest
import tempfile
import os
from unittest.mock import patch

from ue_bp_converter.formatter.base import BaseFormatter
from ue_bp_converter.formatter.plain_formatter import PlainFormatter
from ue_bp_converter.formatter.markdown_formatter import MarkdownFormatter
from ue_bp_converter.formatter.mermaid_formatter import MermaidFormatter
from ue_bp_converter.transformer.models import (
    TransformedGraph,
    TransformedNode,
    DataFlowEdge,
)
from ue_bp_converter.parser.models import PinInfo


@pytest.fixture
def plain_formatter():
    return PlainFormatter()


@pytest.fixture
def markdown_formatter():
    return MarkdownFormatter()


@pytest.fixture
def mermaid_formatter():
    return MermaidFormatter()


def make_pin(name, direction, pin_type, linked_to=None):
    return PinInfo(
        name=name,
        direction=direction,
        pin_type=pin_type,
        linked_to=linked_to or [],
    )


def make_data_pin(name, direction, pin_type):
    return PinInfo(name=name, direction=direction, pin_type=pin_type, linked_to=[])


def make_exec_pin(name, direction):
    return PinInfo(name=name, direction=direction, pin_type="exec", linked_to=[])


def make_node(node_id, label, node_type, pins=None, variables=None, exec_children=None):
    return TransformedNode(
        id=node_id,
        label=label,
        node_type=node_type,
        pins=pins or [],
        variables=variables or [],
        exec_children=exec_children or [],
    )


class TestPlainFormatter:
    def test_format_simple_graph(self, plain_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay", exec_children=[
                    make_node("node_1", "Play Sound", "PlaySound"),
                ]),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
                "node_1": make_node("node_1", "Play Sound", "PlaySound"),
            },
        )
        result = plain_formatter.format(graph)
        assert "[On Begin Play]" in result
        assert "\u2192 [Play Sound]" in result

    def test_format_with_branch(self, plain_formatter):
        true_child = make_node("node_2", "Play Sound", "PlaySound")
        false_child = make_node("node_3", "Print String", "PrintString")
        branch = make_node(
            "node_1", "If/Else Branch", "Branch",
            pins=[
                make_exec_pin("true", "Output"),
                make_exec_pin("false", "Output"),
                make_data_pin("Condition", "Input", "boolean"),
            ],
            exec_children=[true_child, false_child],
        )
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay", exec_children=[branch]),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
                "node_1": branch,
                "node_2": true_child,
                "node_3": false_child,
            },
        )
        result = plain_formatter.format(graph)
        assert "[On Begin Play]" in result
        assert "[If/Else Branch]" in result
        assert "(Condition: boolean)" in result
        assert "True" in result
        assert "False" in result
        assert "[Play Sound]" in result
        assert "[Print String]" in result

    def test_format_with_stats(self, plain_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay"),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
            },
            stats={
                "total_nodes": 1,
                "node_type_counts": {"EventBeginPlay": 1},
                "variable_reads": 2,
                "variable_writes": 1,
                "function_calls": 0,
                "control_flow_nodes": 0,
            },
        )
        result = plain_formatter.format(graph, include_stats=True)
        assert "--- Statistics ---" in result
        assert "Total Nodes: 1" in result
        assert "Variable Reads: 2" in result
        assert "Variable Writes: 1" in result
        assert "Function Calls: 0" in result
        assert "Control Flow Nodes: 0" in result
        assert "EventBeginPlay: 1" in result

    def test_format_with_data_flow(self, plain_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay"),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
                "node_1": make_node("node_1", "If/Else Branch", "Branch"),
            },
            data_flows=[
                DataFlowEdge(
                    source_node="node_1",
                    source_pin="Condition",
                    target_node="node_0",
                    target_pin="ReturnValue",
                    data_type="Boolean",
                ),
            ],
        )
        result = plain_formatter.format(graph)
        assert "--- Data Flow ---" in result
        assert "node_0.ReturnValue" in result
        assert "node_1.Condition" in result
        assert "Boolean" in result

    def test_format_empty_graph(self, plain_formatter):
        graph = TransformedGraph(
            entry_points=[],
            all_nodes={},
            data_flows=[],
        )
        result = plain_formatter.format(graph)
        assert result == ""

    def test_format_with_stats_empty_graph(self, plain_formatter):
        graph = TransformedGraph(
            entry_points=[],
            all_nodes={},
            stats={
                "total_nodes": 0,
                "node_type_counts": {},
                "variable_reads": 0,
                "variable_writes": 0,
                "function_calls": 0,
                "control_flow_nodes": 0,
            },
        )
        result = plain_formatter.format(graph, include_stats=True)
        assert "--- Statistics ---" in result
        assert "Total Nodes: 0" in result

    def test_unknown_node(self, plain_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "[Unknown] SomeUnknownType", "SomeUnknownType"),
            ],
            all_nodes={
                "node_0": make_node("node_0", "[Unknown] SomeUnknownType", "SomeUnknownType"),
            },
        )
        result = plain_formatter.format(graph)
        assert "[Unknown] SomeUnknownType" in result


class TestMarkdownFormatter:
    def test_format_simple_graph(self, markdown_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay", exec_children=[
                    make_node("node_1", "Play Sound", "PlaySound"),
                ]),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
                "node_1": make_node("node_1", "Play Sound", "PlaySound"),
            },
        )
        result = markdown_formatter.format(graph)
        assert "# Blueprint Analysis" in result
        assert "## Node Summary" in result
        assert "## Execution Flow" in result
        assert "| ID | Label | Type | Pins |" in result
        assert "node_0" in result
        assert "On Begin Play" in result
        assert "**On Begin Play**" in result
        assert "**Play Sound**" in result

    def test_format_with_stats(self, markdown_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay"),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
            },
            stats={
                "total_nodes": 1,
                "node_type_counts": {"EventBeginPlay": 1},
                "variable_reads": 2,
                "variable_writes": 1,
                "function_calls": 0,
                "control_flow_nodes": 0,
            },
        )
        result = markdown_formatter.format(graph, include_stats=True)
        assert "## Statistics" in result
        assert "**Total Nodes**: 1" in result
        assert "**Variable Reads**: 2" in result
        assert "**Variable Writes**: 1" in result
        assert "**Function Calls**: 0" in result
        assert "**Control Flow Nodes**: 0" in result
        assert "EventBeginPlay: 1" in result

    def test_format_with_pins(self, markdown_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node(
                    "node_0", "On Begin Play", "EventBeginPlay",
                    pins=[
                        make_exec_pin("then", "Output"),
                        make_data_pin("self", "Output", "object"),
                    ],
                ),
            ],
            all_nodes={
                "node_0": make_node(
                    "node_0", "On Begin Play", "EventBeginPlay",
                    pins=[
                        make_exec_pin("then", "Output"),
                        make_data_pin("self", "Output", "object"),
                    ],
                ),
            },
        )
        result = markdown_formatter.format(graph)
        assert "then(exec)" in result
        assert "self(output:object)" in result

    def test_format_with_data_flow(self, markdown_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay"),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
                "node_1": make_node("node_1", "If/Else Branch", "Branch"),
            },
            data_flows=[
                DataFlowEdge(
                    source_node="node_1", source_pin="Condition",
                    target_node="node_0", target_pin="ReturnValue",
                    data_type="Boolean",
                ),
            ],
        )
        result = markdown_formatter.format(graph)
        assert "## Data Flow" in result
        assert "| From | Pin |" in result
        assert "node_1" in result
        assert "Condition" in result
        assert "ReturnValue" in result

    def test_format_empty_graph(self, markdown_formatter):
        graph = TransformedGraph(entry_points=[], all_nodes={})
        result = markdown_formatter.format(graph)
        assert "# Blueprint Analysis" in result
        assert "## Node Summary" in result
        assert "## Execution Flow" in result
        assert "| ID | Label | Type | Pins |" in result

    def test_unknown_node(self, markdown_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "[Unknown] SomeUnknownType", "SomeUnknownType"),
            ],
            all_nodes={
                "node_0": make_node("node_0", "[Unknown] SomeUnknownType", "SomeUnknownType"),
            },
        )
        result = markdown_formatter.format(graph)
        assert "[Unknown] SomeUnknownType" in result


class TestMermaidFormatter:
    def test_format_simple_graph(self, mermaid_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay", exec_children=[
                    make_node("node_1", "Play Sound", "PlaySound"),
                ]),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
                "node_1": make_node("node_1", "Play Sound", "PlaySound"),
            },
        )
        result = mermaid_formatter.format(graph)
        assert "```mermaid" in result
        assert "flowchart TD" in result
        assert 'node_0["On Begin Play"]' in result
        assert 'node_1["Play Sound"]' in result
        assert "node_0 --> node_1" in result

    def test_format_with_branch_and_labels(self, mermaid_formatter):
        true_child = make_node("node_2", "Play Sound", "PlaySound")
        false_child = make_node("node_3", "Print String", "PrintString")
        branch = make_node(
            "node_1", "If/Else Branch", "Branch",
            pins=[
                make_exec_pin("true", "Output"),
                make_exec_pin("false", "Output"),
            ],
            exec_children=[true_child, false_child],
        )
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay", exec_children=[branch]),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
                "node_1": branch,
                "node_2": true_child,
                "node_3": false_child,
            },
        )
        result = mermaid_formatter.format(graph)
        assert 'node_1 -->|"True"| node_2' in result
        assert 'node_1 -->|"False"| node_3' in result

    def test_format_with_data_flow(self, mermaid_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay", exec_children=[
                    make_node("node_1", "If/Else Branch", "Branch"),
                ]),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
                "node_1": make_node("node_1", "If/Else Branch", "Branch"),
            },
            data_flows=[
                DataFlowEdge(
                    source_node="node_1", source_pin="Condition",
                    target_node="node_0", target_pin="ReturnValue",
                    data_type="Boolean",
                ),
            ],
        )
        result = mermaid_formatter.format(graph)
        assert 'node_1 -.->|"Condition"| node_0' in result

    def test_format_with_stats(self, mermaid_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "On Begin Play", "EventBeginPlay"),
            ],
            all_nodes={
                "node_0": make_node("node_0", "On Begin Play", "EventBeginPlay"),
            },
            stats={
                "total_nodes": 1,
                "variable_reads": 2,
                "variable_writes": 1,
                "function_calls": 0,
                "control_flow_nodes": 0,
            },
        )
        result = mermaid_formatter.format(graph, include_stats=True)
        assert "%% Total Nodes: 1" in result
        assert "%% Variable Reads: 2" in result
        assert "%% Variable Writes: 1" in result
        assert "%% Control Flow Nodes: 0" in result

    def test_format_empty_graph(self, mermaid_formatter):
        graph = TransformedGraph(entry_points=[], all_nodes={})
        result = mermaid_formatter.format(graph)
        assert "```mermaid" in result
        assert "flowchart TD" in result

    def test_unknown_node(self, mermaid_formatter):
        graph = TransformedGraph(
            entry_points=[
                make_node("node_0", "[Unknown] SomeUnknownType", "SomeUnknownType"),
            ],
            all_nodes={
                "node_0": make_node("node_0", "[Unknown] SomeUnknownType", "SomeUnknownType"),
            },
        )
        result = mermaid_formatter.format(graph)
        assert "[Unknown] SomeUnknownType" in result


class TestBaseFormatter:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseFormatter()


class TestCLIIntegration:
    def test_cli_full_pipeline(self):
        from ue_bp_converter.cli import main

        text = """Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
    NodePosX=256
    NodePosY=128
    NodeGuid=ABCDEF0123456789
    CustomFunctionName="EventBeginPlay"
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_branch_exec"
            PinName="then"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_IfThenElse Name="K2Node_IfThenElse_0"
    NodePosX=512
    NodePosY=128
    NodeGuid=1234567890ABCDEF
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_branch_exec"
        PinName="then"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_condition"
        PinName="Condition"
        PinDirection=EGPD_Input
        PinType.PinCategory="boolean"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_true"
        PinName="true"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_false"
        PinName="false"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
End Object"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(text)
            input_path = f.name

        try:
            test_args = [
                "ue-bp-converter",
                "--input", input_path,
                "--format", "plain",
            ]
            with patch("sys.argv", test_args):
                result = main()
                assert result.input == input_path
                assert result.format == "plain"

            test_args_md = [
                "ue-bp-converter",
                "--input", input_path,
                "--format", "markdown",
                "--stats",
            ]
            with patch("sys.argv", test_args_md):
                result = main()
                assert result.format == "markdown"
                assert result.stats is True
        finally:
            os.unlink(input_path)

    def test_cli_with_output_file(self):
        from ue_bp_converter.cli import main

        text = """Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
    CustomFunctionName="EventBeginPlay"
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
End Object"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as input_file:
            input_file.write(text)
            input_path = input_file.name

        output_fd, output_path = tempfile.mkstemp(suffix=".md")
        os.close(output_fd)

        try:
            test_args = [
                "ue-bp-converter",
                "--input", input_path,
                "--format", "markdown",
                "--output", output_path,
            ]
            with patch("sys.argv", test_args):
                main()

            with open(output_path, "r") as f:
                content = f.read()
            assert "# Blueprint Analysis" in content
            assert "On Begin Play" in content
        finally:
            os.unlink(input_path)
            os.unlink(output_path)

    def test_cli_with_mermaid_format(self):
        from ue_bp_converter.cli import main

        text = """Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
    CustomFunctionName="EventBeginPlay"
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
    End Object
End Object"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(text)
            input_path = f.name

        try:
            test_args = [
                "ue-bp-converter",
                "--input", input_path,
                "--format", "mermaid",
                "--stats",
            ]
            with patch("sys.argv", test_args):
                result = main()
                assert result.format == "mermaid"
        finally:
            os.unlink(input_path)