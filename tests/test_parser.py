import pytest
from ue_bp_converter.parser.models import BlueprintGraph, NodeInfo, PinInfo, VariableRef
from ue_bp_converter.parser.blueprint_parser import BlueprintParser


@pytest.fixture
def parser():
    return BlueprintParser()


SIMPLE_EVENT_TEXT = """Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
    NodePosX=256
    NodePosY=128
    NodeGuid=ABCDEF0123456789
    CustomFunctionName="EventBeginPlay"
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        PinType.PinSubCategory=""
        PinType.PinSubCategoryObject=None
    End Object
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="self"
        PinDirection=EGPD_Output
        PinType.PinCategory="object"
        PinType.PinSubCategory=""
        PinType.PinSubCategoryObject=None
    End Object
End Object"""


MULTI_NODE_TEXT = """Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
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
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="self"
        PinDirection=EGPD_Output
        PinType.PinCategory="object"
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


VARIABLE_NODE_TEXT = """Begin Object Class=/Script/Engine.K2Node_VariableGet Name="K2Node_VariableGet_0"
    NodePosX=256
    NodePosY=256
    NodeGuid=AAAA1111BBBB2222
    VariableName="PlayerHealth"
    VariableType="float"
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_var_out"
        PinName="PlayerHealth"
        PinDirection=EGPD_Output
        PinType.PinCategory="float"
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_VariableSet Name="K2Node_VariableSet_0"
    NodePosX=512
    NodePosY=256
    NodeGuid=CCCC3333DDDD4444
    VariableName="PlayerScore"
    VariableType="int"
    bIsEnabled=True
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_var_in"
        PinName="PlayerScore"
        PinDirection=EGPD_Input
        PinType.PinCategory="int"
    End Object
End Object"""


UNKNOWN_NODE_TEXT = """Begin Object Class=/Script/Engine.SomeOtherClass Name="SomeObject_0"
    SomeProperty=123
    AnotherProperty="hello"
End Object
Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_1"
    NodePosX=256
    NodePosY=128
    CustomFunctionName="EventTick"
    bIsEnabled=True
End Object"""


def test_parse_simple_event_node(parser):
    result = parser.parse(SIMPLE_EVENT_TEXT)

    assert isinstance(result, BlueprintGraph)
    assert len(result.nodes) == 1

    node = result.nodes[0]
    assert node.name == "K2Node_Event_0"
    assert node.node_type == "EventBeginPlay"
    assert node.raw_type == "/Script/Engine.K2Node_Event"
    assert node.display_name == "EventBeginPlay"

    assert len(node.pins) == 2

    exec_pin = next(p for p in node.pins if p.pin_type == "exec")
    assert exec_pin.name == "then"
    assert exec_pin.direction == "Output"

    self_pin = next(p for p in node.pins if p.pin_type == "object")
    assert self_pin.name == "self"
    assert self_pin.direction == "Output"

    assert "CustomFunctionName" in node.metadata
    assert node.metadata["CustomFunctionName"] == "EventBeginPlay"


def test_parse_multiple_nodes_and_connections(parser):
    result = parser.parse(MULTI_NODE_TEXT)

    assert len(result.nodes) == 2

    event_node = result.nodes[0]
    assert event_node.node_type == "EventBeginPlay"

    branch_node = result.nodes[1]
    assert branch_node.node_type == "Branch"
    assert branch_node.name == "K2Node_IfThenElse_0"
    assert branch_node.raw_type == "/Script/Engine.K2Node_IfThenElse"

    assert len(branch_node.pins) == 4
    pin_names = [p.name for p in branch_node.pins]
    assert "then" in pin_names
    assert "Condition" in pin_names
    assert "true" in pin_names
    assert "false" in pin_names

    condition_pin = next(p for p in branch_node.pins if p.name == "Condition")
    assert condition_pin.direction == "Input"
    assert condition_pin.pin_type == "boolean"

    assert len(result.exec_flow) > 0
    exec_conn = result.exec_flow[0]
    assert exec_conn[0] == "K2Node_Event_0"
    assert exec_conn[1] == "K2Node_IfThenElse_0"


def test_parse_variable_get_set(parser):
    result = parser.parse(VARIABLE_NODE_TEXT)

    assert len(result.nodes) == 2

    get_node = result.nodes[0]
    assert "Get" in get_node.node_type
    assert "PlayerHealth" in get_node.node_type

    assert len(get_node.variables) == 1
    assert get_node.variables[0].name == "PlayerHealth"
    assert get_node.variables[0].operation == "read"
    assert get_node.variables[0].var_type == "float"

    set_node = result.nodes[1]
    assert "Set" in set_node.node_type
    assert "PlayerScore" in set_node.node_type

    assert len(set_node.variables) == 1
    assert set_node.variables[0].name == "PlayerScore"
    assert set_node.variables[0].operation == "write"
    assert set_node.variables[0].var_type == "int"


def test_parse_unknown_node_type(parser):
    result = parser.parse(UNKNOWN_NODE_TEXT)

    unknown_nodes = [
        n for n in result.nodes if "SomeOtherClass" in n.raw_type
    ]
    assert len(unknown_nodes) == 0

    event_nodes = [n for n in result.nodes if n.node_type == "EventTick"]
    assert len(event_nodes) == 1


def test_parse_empty_text(parser):
    result = parser.parse("")

    assert isinstance(result, BlueprintGraph)
    assert len(result.nodes) == 0
    assert len(result.exec_flow) == 0
    assert len(result.data_flow) == 0


def test_parse_text_with_no_blueprint_nodes(parser):
    text = """Begin Object Class=/Script/Engine.SomeRandomClass Name="Random_0"
    Value=42
End Object"""
    result = parser.parse(text)
    assert len(result.nodes) == 0


def test_parse_node_with_multiple_linked_pins(parser):
    text = """Begin Object Class=/Script/Engine.K2Node_Event Name="EventNode"
    CustomFunctionName="TestEvent"
    Begin Object Class=/Script/Engine.EdGraphPin Name="exec_out"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="target_pin"
            PinName="then"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_IfThenElse Name="BranchNode"
    Begin Object Class=/Script/Engine.EdGraphPin Name="target_pin"
        PinName="then"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
    End Object
End Object"""
    result = parser.parse(text)

    assert len(result.nodes) == 2
    event_node = result.nodes[0]
    assert len(event_node.pins) > 0
    exec_pin = event_node.pins[0]
    assert len(exec_pin.linked_to) > 0


def test_derive_node_type_for_various_nodes(parser):
    from ue_bp_converter.parser.blueprint_parser import BlueprintParser as BP

    test_cases = [
        ("/Script/Engine.K2Node_Event", {"CustomFunctionName": "OnClicked"}, "OnClicked"),
        ("/Script/Engine.K2Node_IfThenElse", {}, "Branch"),
        ("/Script/Engine.K2Node_ForLoop", {}, "ForLoop"),
        ("/Script/Engine.K2Node_ForEachLoop", {}, "ForEachLoop"),
        ("/Script/Engine.K2Node_MathExpression", {}, "MathExpression"),
        ("/Script/Engine.K2Node_Select", {}, "Select"),
        ("/Script/Engine.K2Node_ExecutionSequence", {}, "ExecutionSequence"),
        ("/Script/Engine.K2Node_DynamicCast", {}, "DynamicCast"),
        ("/Script/Engine.K2Node_UnknownType", {}, "K2Node_UnknownType"),
    ]

    p = BP()
    for class_path, props, expected in test_cases:
        result = p._derive_node_type(class_path, props)
        assert result == expected, f"Expected {expected} for {class_path}, got {result}"


def test_mermaid_format_integration(parser):
    result = parser.parse(SIMPLE_EVENT_TEXT)
    assert len(result.nodes) == 1
    node = result.nodes[0]
    assert node.node_type == "EventBeginPlay"
    assert len(node.pins) == 2