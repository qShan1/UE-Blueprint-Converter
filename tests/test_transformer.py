import pytest
from ue_bp_converter.parser.models import BlueprintGraph, NodeInfo, PinInfo, VariableRef
from ue_bp_converter.transformer.models import TransformedGraph, TransformedNode, DataFlowEdge
from ue_bp_converter.transformer.blueprint_transformer import BlueprintTransformer


@pytest.fixture
def transformer():
    return BlueprintTransformer()


def make_node(
    name,
    node_type,
    raw_type="",
    display_name="",
    pins=None,
    variables=None,
    metadata=None,
):
    return NodeInfo(
        name=name,
        node_type=node_type,
        raw_type=raw_type,
        display_name=display_name or node_type,
        pins=pins or [],
        variables=variables or [],
        metadata=metadata or {},
    )


def make_exec_pin(name, direction, linked_to=None):
    return PinInfo(
        name=name,
        direction=direction,
        pin_type="exec",
        linked_to=linked_to or [],
    )


def make_data_pin(name, direction, pin_type, linked_to=None):
    return PinInfo(
        name=name,
        direction=direction,
        pin_type=pin_type,
        linked_to=linked_to or [],
    )


class TestMetadataCleaning:
    def test_removes_bIs_prefix_keys(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node(
                    "Node_0",
                    "EventBeginPlay",
                    metadata={"bIsEnabled": "True", "CustomFunctionName": "EventBeginPlay"},
                )
            ]
        )
        result = transformer.transform(graph)
        assert "bIsEnabled" not in graph.nodes[0].metadata
        assert graph.nodes[0].metadata["CustomFunctionName"] == "EventBeginPlay"

    def test_removes_NodePos_keys(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node(
                    "Node_0",
                    "EventBeginPlay",
                    metadata={"NodePosX": "256", "NodePosY": "128", "SomeKey": "value"},
                )
            ]
        )
        result = transformer.transform(graph)
        assert "NodePosX" not in graph.nodes[0].metadata
        assert "NodePosY" not in graph.nodes[0].metadata
        assert graph.nodes[0].metadata["SomeKey"] == "value"

    def test_removes_Guid_keys(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node(
                    "Node_0",
                    "EventBeginPlay",
                    metadata={
                        "NodeGuid": "ABC123",
                        "SomeGuid": "DEF456",
                        "CustomFunctionName": "EventBeginPlay",
                    },
                )
            ]
        )
        result = transformer.transform(graph)
        assert "NodeGuid" not in graph.nodes[0].metadata
        assert "SomeGuid" not in graph.nodes[0].metadata
        assert graph.nodes[0].metadata["CustomFunctionName"] == "EventBeginPlay"

    def test_removes_CachedNodeTitle_and_PinType_keys(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node(
                    "Node_0",
                    "EventBeginPlay",
                    metadata={
                        "CachedNodeTitle": "MyTitle",
                        "PinType.PinSubCategory": "",
                        "PinType.PinSubCategoryObject": "None",
                        "KeepMe": "stay",
                    },
                )
            ]
        )
        result = transformer.transform(graph)
        assert "CachedNodeTitle" not in graph.nodes[0].metadata
        assert "PinType.PinSubCategory" not in graph.nodes[0].metadata
        assert "PinType.PinSubCategoryObject" not in graph.nodes[0].metadata
        assert graph.nodes[0].metadata["KeepMe"] == "stay"

    def test_cleans_multiple_nodes(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node(
                    "Node_0",
                    "EventBeginPlay",
                    metadata={"bIsEnabled": "True", "NodeGuid": "ABC", "Name": "test"},
                ),
                make_node(
                    "Node_1",
                    "Branch",
                    metadata={"bIsHidden": "False", "NodePosX": "512", "Title": "hello"},
                ),
            ]
        )
        result = transformer.transform(graph)
        assert "bIsEnabled" not in graph.nodes[0].metadata
        assert "NodeGuid" not in graph.nodes[0].metadata
        assert graph.nodes[0].metadata["Name"] == "test"
        assert "bIsHidden" not in graph.nodes[1].metadata
        assert "NodePosX" not in graph.nodes[1].metadata
        assert graph.nodes[1].metadata["Title"] == "hello"


class TestLabelMapping:
    def test_event_begin_play(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("evt", "EventBeginPlay")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "On Begin Play"

    def test_event_tick(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("evt", "EventTick")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "On Tick"

    def test_branch(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("br", "Branch")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "If/Else Branch"

    def test_for_loop(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("fl", "ForLoop")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "For Loop"

    def test_for_each_loop(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("fel", "ForEachLoop")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "For Each Loop"

    def test_execution_sequence(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("seq", "ExecutionSequence")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "Sequence"

    def test_dynamic_cast(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("cast", "DynamicCast")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "Cast To"

    def test_select(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("sel", "Select")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "Select (Ternary)"

    def test_switch(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("sw", "Switch")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "Switch"

    def test_math_expression(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("math", "MathExpression")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "Math Expression"

    def test_binary_operator(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("binop", "BinaryOperator")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "Math Operation"

    def test_call_function_uses_name(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("call", "CallFunction")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "CallFunction"

    def test_input_action_kept_as_is(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("ia", "InputAction (Jump)")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "InputAction (Jump)"

    def test_variable_get_kept_as_is(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("vg", "Health (Get)")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "Health (Get)"

    def test_variable_set_kept_as_is(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("vs", "Score (Set)")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "Score (Set)"

    def test_unknown_prefixed(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("unk", "UnknownNodeType")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "[Unknown] UnknownNodeType"

    def test_unknown_in_name(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("unk", "SomeUnknownType")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "[Unknown] SomeUnknownType"

    def test_unmapped_type_passed_through(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("cust", "CustomEvent_MyEvent")]
        )
        result = transformer.transform(graph)
        assert result.all_nodes["node_0"].label == "CustomEvent_MyEvent"


class TestHierarchicalFlow:
    def test_single_node_no_connections(self, transformer):
        graph = BlueprintGraph(
            nodes=[make_node("evt", "EventBeginPlay")]
        )
        result = transformer.transform(graph)
        assert len(result.entry_points) == 0
        assert len(result.all_nodes) == 1
        assert result.all_nodes["node_0"].label == "On Begin Play"

    def test_simple_event_to_branch_chain(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Event_0", "EventBeginPlay"),
                make_node("Branch_0", "Branch"),
            ],
            exec_flow=[("Event_0", "Branch_0", 0)],
        )
        result = transformer.transform(graph)

        assert len(result.entry_points) == 1
        entry = result.entry_points[0]
        assert entry.label == "On Begin Play"
        assert len(entry.exec_children) == 1
        assert entry.exec_children[0].label == "If/Else Branch"

    def test_multi_level_hierarchy(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Event_0", "EventBeginPlay"),
                make_node("Seq_0", "ExecutionSequence"),
                make_node("Branch_0", "Branch"),
            ],
            exec_flow=[
                ("Event_0", "Seq_0", 0),
                ("Seq_0", "Branch_0", 1),
            ],
        )
        result = transformer.transform(graph)

        assert len(result.entry_points) == 1
        entry = result.entry_points[0]
        assert entry.label == "On Begin Play"
        assert len(entry.exec_children) == 1
        assert entry.exec_children[0].label == "Sequence"
        assert len(entry.exec_children[0].exec_children) == 1
        assert entry.exec_children[0].exec_children[0].label == "If/Else Branch"

    def test_multiple_entry_points(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Event_0", "EventBeginPlay"),
                make_node("Event_1", "EventTick"),
                make_node("Branch_0", "Branch"),
                make_node("Print_0", "PrintString"),
            ],
            exec_flow=[
                ("Event_0", "Branch_0", 0),
                ("Event_1", "Print_0", 0),
            ],
        )
        result = transformer.transform(graph)

        assert len(result.entry_points) == 2
        entry_labels = {e.label for e in result.entry_points}
        assert entry_labels == {"On Begin Play", "On Tick"}

    def test_branch_with_true_false_children(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Event_0", "EventBeginPlay"),
                make_node("Branch_0", "Branch"),
                make_node("PrintTrue", "PrintString"),
                make_node("PrintFalse", "PrintString"),
            ],
            exec_flow=[
                ("Event_0", "Branch_0", 0),
                ("Branch_0", "PrintTrue", 1),
                ("Branch_0", "PrintFalse", 2),
            ],
        )
        result = transformer.transform(graph)

        assert len(result.entry_points) == 1
        entry = result.entry_points[0]
        assert len(entry.exec_children) == 1
        branch = entry.exec_children[0]
        assert branch.label == "If/Else Branch"
        assert len(branch.exec_children) == 2

    def test_orphan_node_present(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Event_0", "EventBeginPlay"),
                make_node("Branch_0", "Branch"),
                make_node("Orphan", "SomeNode"),
            ],
            exec_flow=[("Event_0", "Branch_0", 0)],
        )
        result = transformer.transform(graph)

        assert len(result.all_nodes) == 3
        orphan = [n for n in result.all_nodes.values() if n.label == "SomeNode"]
        assert len(orphan) == 1

    def test_node_ids_are_unique_sequential(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Event_0", "EventBeginPlay"),
                make_node("Branch_0", "Branch"),
            ],
            exec_flow=[("Event_0", "Branch_0", 0)],
        )
        result = transformer.transform(graph)

        ids = sorted(result.all_nodes.keys())
        assert ids == ["node_0", "node_1"]


class TestDataFlow:
    def test_data_flow_edges_created(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Get_0", "Health (Get)", pins=[
                    make_data_pin("Health", "Output", "float"),
                ]),
                make_node("Branch_0", "Branch", pins=[
                    make_data_pin("Condition", "Input", "boolean"),
                ]),
            ],
            data_flow=[("Get_0", "Health", "Branch_0", "Condition")],
        )
        result = transformer.transform(graph)

        assert len(result.data_flows) == 1
        edge = result.data_flows[0]
        assert edge.source_node == "node_0"
        assert edge.source_pin == "Health"
        assert edge.target_node == "node_1"
        assert edge.target_pin == "Condition"
        assert edge.data_type == "float"

    def test_data_flow_with_unknown_type(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Src", "SomeNode", pins=[
                    make_data_pin("Out", "Output", ""),
                ]),
                make_node("Dst", "OtherNode", pins=[
                    make_data_pin("In", "Input", ""),
                ]),
            ],
            data_flow=[("Src", "Out", "Dst", "In")],
        )
        result = transformer.transform(graph)

        assert len(result.data_flows) == 1
        assert result.data_flows[0].data_type == ""

    def test_data_flow_skips_unknown_nodes(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("Known", "SomeNode"),
            ],
            data_flow=[("Known", "Out", "Unknown", "In")],
        )
        result = transformer.transform(graph)

        assert len(result.data_flows) == 0


class TestStats:
    def test_total_node_count(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("evt", "EventBeginPlay"),
                make_node("br", "Branch"),
                make_node("loop", "ForLoop"),
            ]
        )
        result = transformer.transform(graph)
        assert result.stats["total_nodes"] == 3

    def test_node_type_counts(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("evt", "EventBeginPlay"),
                make_node("br", "Branch"),
                make_node("br2", "Branch"),
                make_node("loop", "ForLoop"),
            ]
        )
        result = transformer.transform(graph)
        assert result.stats["node_type_counts"]["EventBeginPlay"] == 1
        assert result.stats["node_type_counts"]["Branch"] == 2
        assert result.stats["node_type_counts"]["ForLoop"] == 1

    def test_variable_counts(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("get", "Health (Get)", variables=[
                    VariableRef(name="Health", operation="read", var_type="float"),
                ]),
                make_node("set", "Score (Set)", variables=[
                    VariableRef(name="Score", operation="write", var_type="int"),
                ]),
                make_node("get2", "Ammo (Get)", variables=[
                    VariableRef(name="Ammo", operation="read", var_type="int"),
                ]),
            ]
        )
        result = transformer.transform(graph)
        assert result.stats["variable_reads"] == 2
        assert result.stats["variable_writes"] == 1

    def test_function_call_count(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("call1", "PrintString", raw_type="K2Node_CallFunction"),
                make_node("call2", "Delay", raw_type="K2Node_CallFunction"),
                make_node("evt", "EventBeginPlay", raw_type="K2Node_Event"),
            ]
        )
        result = transformer.transform(graph)
        assert result.stats["function_calls"] == 2

    def test_control_flow_count(self, transformer):
        graph = BlueprintGraph(
            nodes=[
                make_node("br", "Branch"),
                make_node("fl", "ForLoop"),
                make_node("fel", "ForEachLoop"),
                make_node("sw", "Switch"),
                make_node("sel", "Select"),
                make_node("evt", "EventBeginPlay"),
            ]
        )
        result = transformer.transform(graph)
        assert result.stats["control_flow_nodes"] == 5

    def test_stats_on_empty_graph(self, transformer):
        graph = BlueprintGraph(nodes=[])
        result = transformer.transform(graph)
        assert result.stats["total_nodes"] == 0
        assert result.stats["node_type_counts"] == {}
        assert result.stats["variable_reads"] == 0
        assert result.stats["variable_writes"] == 0
        assert result.stats["function_calls"] == 0
        assert result.stats["control_flow_nodes"] == 0


class TestEmptyGraph:
    def test_empty_graph(self, transformer):
        graph = BlueprintGraph(nodes=[], exec_flow=[], data_flow=[])
        result = transformer.transform(graph)

        assert isinstance(result, TransformedGraph)
        assert len(result.entry_points) == 0
        assert len(result.all_nodes) == 0
        assert len(result.data_flows) == 0
        assert result.stats["total_nodes"] == 0


class TestIntegrationWithParser:
    def test_parse_then_transform_simple_event(self, transformer):
        from ue_bp_converter.parser.blueprint_parser import BlueprintParser

        parser = BlueprintParser()
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
    End Object
End Object"""

        graph = parser.parse(text)
        result = transformer.transform(graph)

        assert len(result.all_nodes) == 1
        node = list(result.all_nodes.values())[0]
        assert node.label == "On Begin Play"
        assert node.node_type == "EventBeginPlay"
        assert len(node.pins) == 1

    def test_parse_then_transform_with_exec_flow(self, transformer):
        from ue_bp_converter.parser.blueprint_parser import BlueprintParser

        parser = BlueprintParser()
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
End Object"""

        graph = parser.parse(text)
        result = transformer.transform(graph)

        assert len(result.all_nodes) == 2
        assert len(result.entry_points) == 1
        assert result.entry_points[0].label == "On Begin Play"
        assert len(result.entry_points[0].exec_children) == 1
        assert result.entry_points[0].exec_children[0].label == "If/Else Branch"


def test_transform_cleans_metadata(transformer):
    graph = BlueprintGraph(
        nodes=[
            make_node(
                "n0",
                "EventBeginPlay",
                metadata={
                    "bIsEnabled": "True",
                    "NodePosX": "256",
                    "NodeGuid": "ABC",
                    "CustomFunctionName": "EventBeginPlay",
                    "CachedNodeTitle": "Old Title",
                },
            )
        ]
    )
    result = transformer.transform(graph)
    remaining = graph.nodes[0].metadata
    assert "bIsEnabled" not in remaining
    assert "NodePosX" not in remaining
    assert "NodeGuid" not in remaining
    assert "CachedNodeTitle" not in remaining
    assert remaining["CustomFunctionName"] == "EventBeginPlay"


def test_transform_node_label_mapping(transformer):
    type_label_pairs = [
        ("EventBeginPlay", "On Begin Play"),
        ("EventTick", "On Tick"),
        ("Branch", "If/Else Branch"),
        ("ForLoop", "For Loop"),
        ("ForEachLoop", "For Each Loop"),
        ("ExecutionSequence", "Sequence"),
        ("DynamicCast", "Cast To"),
        ("Select", "Select (Ternary)"),
        ("Switch", "Switch"),
        ("MathExpression", "Math Expression"),
        ("BinaryOperator", "Math Operation"),
    ]
    nodes = [make_node(f"n{i}", nt) for i, (nt, _) in enumerate(type_label_pairs)]
    graph = BlueprintGraph(nodes=nodes)
    result = transformer.transform(graph)
    for i, (nt, expected_label) in enumerate(type_label_pairs):
        node_id = f"node_{i}"
        assert result.all_nodes[node_id].label == expected_label, (
            f"Mismatch for {nt}: expected {expected_label}, got {result.all_nodes[node_id].label}"
        )


def test_transform_builds_hierarchical_flow(transformer):
    graph = BlueprintGraph(
        nodes=[
            make_node("evt", "EventBeginPlay"),
            make_node("seq", "ExecutionSequence"),
            make_node("br", "Branch"),
            make_node("print_true", "PrintString"),
            make_node("print_false", "PrintString"),
        ],
        exec_flow=[
            ("evt", "seq", 0),
            ("seq", "br", 1),
            ("br", "print_true", 2),
            ("br", "print_false", 3),
        ],
    )
    result = transformer.transform(graph)

    assert len(result.entry_points) == 1
    entry = result.entry_points[0]
    assert entry.label == "On Begin Play"
    assert len(entry.exec_children) == 1
    seq = entry.exec_children[0]
    assert seq.label == "Sequence"
    assert len(seq.exec_children) == 1
    branch = seq.exec_children[0]
    assert branch.label == "If/Else Branch"
    assert len(branch.exec_children) == 2
    child_labels = {c.label for c in branch.exec_children}
    assert child_labels == {"PrintString", "PrintString"}


def test_transform_generates_stats(transformer):
    graph = BlueprintGraph(
        nodes=[
            make_node("evt", "EventBeginPlay", raw_type="K2Node_Event"),
            make_node("br", "Branch"),
            make_node("call", "PrintString", raw_type="K2Node_CallFunction"),
            make_node("get", "Health (Get)", variables=[
                VariableRef(name="Health", operation="read", var_type="float"),
            ]),
            make_node("set", "Score (Set)", variables=[
                VariableRef(name="Score", operation="write", var_type="int"),
            ]),
            make_node("loop", "ForLoop"),
        ]
    )
    result = transformer.transform(graph)

    assert result.stats["total_nodes"] == 6
    assert result.stats["variable_reads"] == 1
    assert result.stats["variable_writes"] == 1
    assert result.stats["function_calls"] == 1
    assert result.stats["control_flow_nodes"] == 2


def test_transform_empty_graph(transformer):
    graph = BlueprintGraph(nodes=[], exec_flow=[], data_flow=[])
    result = transformer.transform(graph)

    assert isinstance(result, TransformedGraph)
    assert len(result.entry_points) == 0
    assert len(result.all_nodes) == 0
    assert len(result.data_flows) == 0
    assert result.stats["total_nodes"] == 0