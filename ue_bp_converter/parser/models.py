from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PinInfo:
    name: str
    direction: str
    pin_type: str
    linked_to: list[str] = field(default_factory=list)


@dataclass
class VariableRef:
    name: str
    operation: str
    var_type: Optional[str] = None


@dataclass
class NodeInfo:
    name: str
    node_type: str
    raw_type: str
    display_name: str
    pins: list[PinInfo] = field(default_factory=list)
    variables: list[VariableRef] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class BlueprintGraph:
    nodes: list[NodeInfo] = field(default_factory=list)
    exec_flow: list[tuple[str, str, int]] = field(default_factory=list)
    data_flow: list[tuple[str, str, str, str]] = field(default_factory=list)