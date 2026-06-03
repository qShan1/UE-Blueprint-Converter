import argparse
import sys

from .parser.blueprint_parser import BlueprintParser
from .transformer.blueprint_transformer import BlueprintTransformer
from .formatter.plain_formatter import PlainFormatter
from .formatter.markdown_formatter import MarkdownFormatter
from .formatter.mermaid_formatter import MermaidFormatter


def create_formatter(format_name: str):
    formatters = {
        "plain": PlainFormatter,
        "markdown": MarkdownFormatter,
        "mermaid": MermaidFormatter,
    }
    cls = formatters.get(format_name)
    if cls is None:
        raise ValueError(f"Unknown format: {format_name}")
    return cls()


def main() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="UE Blueprint Converter - Convert blueprints to various formats"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Input file path (default: stdin)",
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        default="plain",
        choices=["plain", "markdown", "mermaid"],
        help="Output format (default: plain)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Output statistics",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()

    if args.input:
        with open(args.input, "r") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    bp_parser = BlueprintParser()
    graph = bp_parser.parse(text)

    transformer = BlueprintTransformer()
    transformed = transformer.transform(graph)

    formatter = create_formatter(args.format)
    result = formatter.format(transformed, include_stats=args.stats)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
    else:
        print(result, end="")

    return args