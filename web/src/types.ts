export interface PinInfo {
  name: string;
  direction: string;
  pin_type: string;
  linked_to: string[];
}

export interface VariableRef {
  name: string;
  operation: string;
  var_type: string | null;
}

export interface TransformedNode {
  id: string;
  label: string;
  node_type: string;
  pins: PinInfo[];
  variables: VariableRef[];
  exec_children: TransformedNode[];
}

export interface DataFlowEdge {
  source_node: string;
  source_pin: string;
  target_node: string;
  target_pin: string;
  data_type: string;
}

export interface TransformedGraph {
  entry_points: TransformedNode[];
  all_nodes: Record<string, TransformedNode>;
  data_flows: DataFlowEdge[];
  stats: Record<string, any>;
}

export type ViewMode = 'graph' | 'plain' | 'markdown' | 'mermaid';