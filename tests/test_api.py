import os

import pytest
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def read_example(filename: str) -> str:
    path = os.path.join(EXAMPLES_DIR, filename)
    with open(path, "r") as f:
        return f.read()


SIMPLE_EVENT = read_example("simple_event.blueprint")
BRANCH_FLOW = read_example("branch_flow.blueprint")
VARIABLE_LOOP = read_example("variable_and_loop.blueprint")


class TestParseEndpoint:
    def test_parse_simple_event(self):
        resp = client.post("/api/parse", json={"text": SIMPLE_EVENT})
        assert resp.status_code == 200
        data = resp.json()

        assert "entry_points" in data
        assert "all_nodes" in data
        assert "data_flows" in data
        assert "stats" in data

        assert len(data["entry_points"]) > 0
        assert len(data["all_nodes"]) > 0
        assert data["stats"]["total_nodes"] > 0

        entry = data["entry_points"][0]
        assert "id" in entry
        assert "label" in entry
        assert "node_type" in entry
        assert "pins" in entry
        assert "exec_children" in entry

    def test_parse_branch_flow(self):
        resp = client.post("/api/parse", json={"text": BRANCH_FLOW})
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["entry_points"]) >= 1
        assert data["stats"]["total_nodes"] >= 3
        assert data["stats"]["control_flow_nodes"] >= 1

    def test_parse_variable_loop(self):
        resp = client.post("/api/parse", json={"text": VARIABLE_LOOP})
        assert resp.status_code == 200
        data = resp.json()

        assert len(data["all_nodes"]) >= 3
        assert data["stats"]["variable_reads"] >= 1 or data["stats"]["variable_writes"] >= 1

    def test_parse_empty_text(self):
        resp = client.post("/api/parse", json={"text": ""})
        assert resp.status_code == 400

    def test_parse_invalid_json(self):
        resp = client.post("/api/parse", json={})
        assert resp.status_code == 422


class TestFormatEndpoint:
    def test_format_plain(self):
        resp = client.post(
            "/api/format",
            json={"text": SIMPLE_EVENT, "format": "plain"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert "[On Begin Play]" in data["result"]
        assert "[PrintString]" in data["result"]

    def test_format_plain_with_stats(self):
        resp = client.post(
            "/api/format",
            json={"text": SIMPLE_EVENT, "format": "plain", "stats": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "--- Statistics ---" in data["result"]

    def test_format_markdown(self):
        resp = client.post(
            "/api/format",
            json={"text": BRANCH_FLOW, "format": "markdown"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "# Blueprint Analysis" in data["result"]
        assert "## Node Summary" in data["result"]
        assert "## Execution Flow" in data["result"]

    def test_format_markdown_with_stats(self):
        resp = client.post(
            "/api/format",
            json={"text": BRANCH_FLOW, "format": "markdown", "stats": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "## Statistics" in data["result"]

    def test_format_mermaid(self):
        resp = client.post(
            "/api/format",
            json={"text": SIMPLE_EVENT, "format": "mermaid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "```mermaid" in data["result"]
        assert "flowchart TD" in data["result"]
        assert "-->" in data["result"]

    def test_format_mermaid_with_stats(self):
        resp = client.post(
            "/api/format",
            json={"text": VARIABLE_LOOP, "format": "mermaid", "stats": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "%% Total Nodes:" in data["result"]

    def test_format_invalid_format(self):
        resp = client.post(
            "/api/format",
            json={"text": SIMPLE_EVENT, "format": "invalid"},
        )
        assert resp.status_code == 422

    def test_format_empty_text(self):
        resp = client.post(
            "/api/format",
            json={"text": "", "format": "plain"},
        )
        assert resp.status_code == 400


class TestExamplesEndpoint:
    def test_list_examples(self):
        resp = client.get("/api/examples")
        assert resp.status_code == 200
        data = resp.json()
        assert "examples" in data
        assert "simple_event" in data["examples"]
        assert "branch_flow" in data["examples"]
        assert "variable_and_loop" in data["examples"]

    def test_get_example_simple_event(self):
        resp = client.get("/api/examples/simple_event")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "simple_event"
        assert "Begin Object" in data["content"]

    def test_get_example_branch_flow(self):
        resp = client.get("/api/examples/branch_flow")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "branch_flow"
        assert "K2Node_IfThenElse" in data["content"]

    def test_get_example_variable_and_loop(self):
        resp = client.get("/api/examples/variable_and_loop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "variable_and_loop"
        assert "K2Node_ForLoop" in data["content"]

    def test_get_example_not_found(self):
        resp = client.get("/api/examples/nonexistent")
        assert resp.status_code == 404