import dataclasses
import json
import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ue_bp_converter.parser.blueprint_parser import BlueprintParser
from ue_bp_converter.transformer.blueprint_transformer import BlueprintTransformer
from ue_bp_converter.transformer.models import TransformedGraph, TransformedNode
from ue_bp_converter.formatter.plain_formatter import PlainFormatter
from ue_bp_converter.formatter.markdown_formatter import MarkdownFormatter
from ue_bp_converter.formatter.mermaid_formatter import MermaidFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(HERE, "web", "dist")

app = FastAPI(title="UE Blueprint Converter API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")

EXAMPLES_MAP: dict[str, str] = {
    "simple_event": "simple_event.blueprint",
    "branch_flow": "branch_flow.blueprint",
    "variable_and_loop": "variable_and_loop.blueprint",
}

parser = BlueprintParser()
transformer = BlueprintTransformer()
formatters = {
    "plain": PlainFormatter(),
    "markdown": MarkdownFormatter(),
    "mermaid": MermaidFormatter(),
}


class ParseRequest(BaseModel):
    text: str


class FormatRequest(BaseModel):
    text: str
    format: Literal["plain", "markdown", "mermaid"] = "plain"
    stats: bool = False


def _node_to_dict(node: TransformedNode) -> dict[str, Any]:
    return {
        "id": node.id,
        "label": node.label,
        "node_type": node.node_type,
        "pins": [dataclasses.asdict(p) for p in node.pins],
        "variables": [dataclasses.asdict(v) for v in node.variables],
        "exec_children": [_node_to_dict(c) for c in node.exec_children],
    }


def _graph_to_dict(graph: TransformedGraph) -> dict[str, Any]:
    return {
        "entry_points": [_node_to_dict(ep) for ep in graph.entry_points],
        "all_nodes": {
            nid: _node_to_dict(n) for nid, n in graph.all_nodes.items()
        },
        "data_flows": [dataclasses.asdict(df) for df in graph.data_flows],
        "stats": graph.stats,
    }


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def _parse_and_transform(text: str) -> TransformedGraph:
    bp_graph = parser.parse(text)
    return transformer.transform(bp_graph)


@app.post("/api/parse")
def parse_endpoint(req: ParseRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    try:
        transformed = _parse_and_transform(req.text)
        return _graph_to_dict(transformed)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/format")
def format_endpoint(req: FormatRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    formatter = formatters.get(req.format)
    if formatter is None:
        raise HTTPException(status_code=400, detail=f"Unknown format: {req.format}")
    try:
        transformed = _parse_and_transform(req.text)
        result = formatter.format(transformed, include_stats=req.stats)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/examples")
def list_examples():
    return {"examples": list(EXAMPLES_MAP.keys())}


@app.get("/api/examples/{name}")
def get_example(name: str):
    filename = EXAMPLES_MAP.get(name)
    if filename is None:
        raise HTTPException(status_code=404, detail=f"Example '{name}' not found")
    filepath = os.path.join(EXAMPLES_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail=f"Example file '{filename}' not found")
    with open(filepath, "r") as f:
        content = f.read()
    return {"name": name, "content": content}


if os.path.isdir(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        file_path = os.path.join(DIST_DIR, full_path) if full_path else os.path.join(DIST_DIR, "index.html")
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(DIST_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Not found")