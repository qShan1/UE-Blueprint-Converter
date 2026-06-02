from dataclasses import dataclass, field


@dataclass
class TransformedNode:
    id: str
    label: str
    node_type: str
    pins: list = field(default_factory=list)
    variables: list = field(default_factory=list)
    exec_children: list = field(default_factory=list)


@dataclass
class DataFlowEdge:
    source_node: str
    source_pin: str
    target_node: str
    target_pin: str
    data_type: str


@dataclass
class TransformedGraph:
    entry_points: list[TransformedNode] = field(default_factory=list)
    all_nodes: dict[str, TransformedNode] = field(default_factory=dict)
    data_flows: list[DataFlowEdge] = field(default_factory=list)
    stats: dict = field(default_factory=dict)