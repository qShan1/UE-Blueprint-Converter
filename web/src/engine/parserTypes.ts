/** Intermediate types for the raw parsed blueprint (before transformation) */

export interface RawObject {
  class_path: string
  name: string
  properties: Record<string, string>
  children: RawObject[]
}

export interface PinInfo {
  name: string
  direction: string
  pin_type: string
  linked_to: string[]
}

export interface VariableRef {
  name: string
  operation: string
  var_type: string | null
}

export interface NodeInfo {
  name: string
  node_type: string
  raw_type: string
  display_name: string
  pins: PinInfo[]
  variables: VariableRef[]
  metadata: Record<string, string>
}

export interface BlueprintGraph {
  nodes: NodeInfo[]
  exec_flow: [string, string, number][]
  data_flow: [string, string, string, string][]
}