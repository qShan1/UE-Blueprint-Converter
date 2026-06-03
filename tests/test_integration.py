import pytest
import os
import sys
import io
import tempfile
from unittest.mock import patch

from ue_bp_converter.cli import main
from ue_bp_converter.parser.blueprint_parser import BlueprintParser
from ue_bp_converter.transformer.blueprint_transformer import BlueprintTransformer
from ue_bp_converter.formatter.plain_formatter import PlainFormatter
from ue_bp_converter.formatter.markdown_formatter import MarkdownFormatter
from ue_bp_converter.formatter.mermaid_formatter import MermaidFormatter

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


@pytest.fixture
def parser():
    return BlueprintParser()


@pytest.fixture
def transformer():
    return BlueprintTransformer()


@pytest.fixture
def plain_formatter():
    return PlainFormatter()


@pytest.fixture
def markdown_formatter():
    return MarkdownFormatter()


@pytest.fixture
def mermaid_formatter():
    return MermaidFormatter()


def read_example(filename):
    path = os.path.join(EXAMPLES_DIR, filename)
    with open(path, "r") as f:
        return f.read()


class TestFullPipelinePlain:
    def test_full_pipeline_simple_event(self, parser, transformer, plain_formatter):
        text = read_example("simple_event.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = plain_formatter.format(transformed)

        assert "[On Begin Play]" in result
        assert "[PrintString]" in result
        assert "self: object" in result
        assert "InString: string" in result

    def test_full_pipeline_branch_flow(self, parser, transformer, plain_formatter):
        text = read_example("branch_flow.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = plain_formatter.format(transformed)

        assert "[If/Else Branch]" in result
        assert "True " in result
        assert "False " in result
        assert "[PrintString]" in result
        assert "[Delay]" in result

    def test_full_pipeline_variable_loop(self, parser, transformer, plain_formatter):
        text = read_example("variable_and_loop.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = plain_formatter.format(transformed)

        assert "[For Loop]" in result
        assert "[Counter (Set)]" in result


class TestFullPipelineMarkdown:
    def test_markdown_format_integration(self, parser, transformer, markdown_formatter):
        text = read_example("simple_event.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = markdown_formatter.format(transformed)

        assert "# Blueprint Analysis" in result
        assert "## Node Summary" in result
        assert "## Execution Flow" in result
        assert "| ID | Label | Type | Pins |" in result
        assert "On Begin Play" in result

    def test_markdown_with_branch(self, parser, transformer, markdown_formatter):
        text = read_example("branch_flow.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = markdown_formatter.format(transformed)

        assert "If/Else Branch" in result
        assert "Condition(exec)" in result or "then(exec)" in result


class TestFullPipelineMermaid:
    def test_mermaid_format_integration(self, parser, transformer, mermaid_formatter):
        text = read_example("simple_event.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = mermaid_formatter.format(transformed)

        assert "```mermaid" in result
        assert "flowchart TD" in result
        assert "-->" in result
        assert "On Begin Play" in result

    def test_mermaid_with_branch(self, parser, transformer, mermaid_formatter):
        text = read_example("branch_flow.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = mermaid_formatter.format(transformed)

        assert 'node_1["If/Else Branch"]' in result
        assert "node_1 -->" in result


class TestStatsIntegration:
    def test_stats_integration_plain(self, parser, transformer, plain_formatter):
        text = read_example("branch_flow.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = plain_formatter.format(transformed, include_stats=True)

        assert "--- Statistics ---" in result
        assert "Total Nodes:" in result
        assert "Node Type Counts:" in result
        assert "Control Flow Nodes:" in result

    def test_stats_integration_markdown(self, parser, transformer, markdown_formatter):
        text = read_example("simple_event.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = markdown_formatter.format(transformed, include_stats=True)

        assert "## Statistics" in result
        assert "Total Nodes" in result

    def test_stats_integration_mermaid(self, parser, transformer, mermaid_formatter):
        text = read_example("simple_event.blueprint")
        graph = parser.parse(text)
        transformed = transformer.transform(graph)
        result = mermaid_formatter.format(transformed, include_stats=True)

        assert "%% Total Nodes:" in result
        assert "%% Function Calls:" in result


class TestCLIIntegration:
    def test_cli_examples_simple_event(self):
        input_path = os.path.join(EXAMPLES_DIR, "simple_event.blueprint")

        test_args = [
            "ue-bp-converter",
            "--input", input_path,
            "--format", "plain",
        ]
        with patch("sys.argv", test_args):
            stdout = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = stdout
            try:
                result = main()
            finally:
                sys.stdout = old_stdout

            assert result.input == input_path
            assert result.format == "plain"

        output = stdout.getvalue()
        assert "[On Begin Play]" in output
        assert "[PrintString]" in output

    def test_cli_examples_branch_markdown(self):
        input_path = os.path.join(EXAMPLES_DIR, "branch_flow.blueprint")

        test_args = [
            "ue-bp-converter",
            "--input", input_path,
            "--format", "markdown",
            "--stats",
        ]
        with patch("sys.argv", test_args):
            stdout = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = stdout
            try:
                result = main()
            finally:
                sys.stdout = old_stdout

            assert result.format == "markdown"
            assert result.stats is True

        output = stdout.getvalue()
        assert "# Blueprint Analysis" in output
        assert "## Statistics" in output

    def test_cli_examples_loop_mermaid(self):
        input_path = os.path.join(EXAMPLES_DIR, "variable_and_loop.blueprint")

        test_args = [
            "ue-bp-converter",
            "--input", input_path,
            "--format", "mermaid",
        ]
        with patch("sys.argv", test_args):
            stdout = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = stdout
            try:
                result = main()
            finally:
                sys.stdout = old_stdout

            assert result.format == "mermaid"

        output = stdout.getvalue()
        assert "```mermaid" in output
        assert "flowchart TD" in output

    def test_cli_with_output_file(self):
        input_path = os.path.join(EXAMPLES_DIR, "simple_event.blueprint")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            output_path = f.name

        try:
            test_args = [
                "ue-bp-converter",
                "--input", input_path,
                "--format", "plain",
                "--output", output_path,
            ]
            with patch("sys.argv", test_args):
                main()

            with open(output_path, "r") as f:
                content = f.read()
            assert "[On Begin Play]" in content
        finally:
            os.unlink(output_path)


class TestAllExamples:
    def test_all_examples_parse_successfully(self, parser):
        for fname in ["simple_event.blueprint", "branch_flow.blueprint", "variable_and_loop.blueprint"]:
            text = read_example(fname)
            graph = parser.parse(text)
            assert graph is not None
            assert len(graph.nodes) > 0, f"{fname} should produce at least one node"

    def test_all_examples_transform_successfully(self, parser, transformer):
        for fname in ["simple_event.blueprint", "branch_flow.blueprint", "variable_and_loop.blueprint"]:
            text = read_example(fname)
            graph = parser.parse(text)
            transformed = transformer.transform(graph)
            assert transformed is not None
            assert len(transformed.all_nodes) > 0, f"{fname} should produce at least one transformed node"

    def test_all_examples_produce_entry_points(self, parser, transformer):
        for fname in ["simple_event.blueprint", "branch_flow.blueprint", "variable_and_loop.blueprint"]:
            text = read_example(fname)
            graph = parser.parse(text)
            transformed = transformer.transform(graph)
            assert len(transformed.entry_points) > 0, f"{fname} should have at least one entry point"