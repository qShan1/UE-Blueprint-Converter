/**
 * Transforms a parsed BlueprintGraph into a TransformedGraph (tree structure for UI).
 * Translates Python transformer at ue_bp_converter/transformer/blueprint_transformer.py
 */

import type { BlueprintGraph, NodeInfo, PinInfo, VariableRef } from './parserTypes'
import type { TransformedGraph, TransformedNode, DataFlowEdge } from '../types'

const LABEL_MAP: Record<string, string> = {
  EventBeginPlay: 'On Begin Play',
  EventTick: 'On Tick',
  Branch: 'If/Else Branch',
  ForLoop: 'For Loop',
  ForEachLoop: 'For Each Loop',
  ExecutionSequence: 'Sequence',
  DynamicCast: 'Cast To',
  Select: 'Select (Ternary)',
  Switch: 'Switch',
  MathExpression: 'Math Expression',
  BinaryOperator: 'Math Operation',
}

const METADATA_CLEAN_PREFIXES = ['bIs', 'NodePos', 'PinType']
const METADATA_CLEAN_EXACT = new Set(['NodeGuid', 'CachedNodeTitle'])

const CONTROL_FLOW_TYPES = new Set(['Branch', 'ForLoop', 'ForEachLoop', 'Switch', 'Select'])

export class BlueprintTransformer {
  transform(graph: BlueprintGraph): TransformedGraph {
    this._cleanMetadata(graph)

    const nameToNode = new Map<string, NodeInfo>()
    for (const n of graph.nodes) nameToNode.set(n.name, n)

    // Build exec adjacency
    const childrenOf = new Map<string, [string, number][]>()
    for (const [src, tgt, order] of graph.exec_flow) {
      if (!childrenOf.has(src)) childrenOf.set(src, [])
      childrenOf.get(src)!.push([tgt, order])
    }
    for (const [, list] of childrenOf) list.sort((a, b) => a[1] - b[1])

    // Find entry points
    const allSources = new Set(graph.exec_flow.map(e => e[0]))
    const allTargets = new Set(graph.exec_flow.map(e => e[1]))
    const entryNames = graph.nodes.filter(n => allSources.has(n.name) && !allTargets.has(n.name)).map(n => n.name)

    const nameToId = new Map<string, string>()
    const allNodes = new Map<string, TransformedNode>()
    let idCounter = 0

    const buildTransformed = (name: string): string => {
      if (nameToId.has(name)) return nameToId.get(name)!
      const nodeInfo = nameToNode.get(name)
      if (!nodeInfo) return ''

      const label = this._mapLabel(nodeInfo.node_type)
      const nodeId = `node_${idCounter++}`
      nameToId.set(name, nodeId)

      const tnode: TransformedNode = {
        id: nodeId,
        label,
        node_type: nodeInfo.node_type,
        pins: nodeInfo.pins as unknown as PinInfo[],
        variables: nodeInfo.variables as unknown as VariableRef[],
        exec_children: [],
      }
      allNodes.set(nodeId, tnode)

      const childNames = (childrenOf.get(name) || []).map(([tgt]) => tgt)
      for (const childName of childNames) {
        if (nameToNode.has(childName) && !nameToId.has(childName)) {
          const childId = buildTransformed(childName)
          if (childId) {
            const childNode = allNodes.get(childId)
            if (childNode) tnode.exec_children.push(childNode)
          }
        }
      }

      return nodeId
    }

    const entryNodes: TransformedNode[] = []
    for (const name of entryNames) {
      if (nameToNode.has(name)) {
        buildTransformed(name)
        const nid = nameToId.get(name)!
        const node = allNodes.get(nid)
        if (node) entryNodes.push(node)
      }
    }

    // Add orphan nodes
    for (const node of graph.nodes) {
      if (!nameToId.has(node.name)) {
        const label = this._mapLabel(node.node_type)
        const nodeId = `node_${idCounter++}`
        nameToId.set(node.name, nodeId)
        allNodes.set(nodeId, {
          id: nodeId,
          label,
          node_type: node.node_type,
          pins: node.pins as unknown as PinInfo[],
          variables: node.variables as unknown as VariableRef[],
          exec_children: [],
        })
      }
    }

    // Build data flows
    const dataFlows: DataFlowEdge[] = []
    for (const [srcName, srcPin, tgtName, tgtPin] of graph.data_flow) {
      const srcId = nameToId.get(srcName)
      const tgtId = nameToId.get(tgtName)
      if (!srcId || !tgtId) continue

      let dataType = ''
      const srcNode = nameToNode.get(srcName)
      if (srcNode) {
        const pin = srcNode.pins.find(p => p.name === srcPin)
        if (pin) dataType = pin.pin_type
      }

      dataFlows.push({
        source_node: srcId,
        source_pin: srcPin,
        target_node: tgtId,
        target_pin: tgtPin,
        data_type: dataType,
      })
    }

    // Generate stats
    const stats = this._generateStats(graph)

    return {
      entry_points: entryNodes,
      all_nodes: Object.fromEntries(allNodes),
      data_flows: dataFlows,
      stats,
    }
  }

  private _cleanMetadata(graph: BlueprintGraph): void {
    for (const node of graph.nodes) {
      const keysToRemove: string[] = []
      for (const key of Object.keys(node.metadata)) {
        if (METADATA_CLEAN_EXACT.has(key) || METADATA_CLEAN_PREFIXES.some(p => key.startsWith(p))) {
          keysToRemove.push(key)
        }
      }
      for (const key of keysToRemove) delete node.metadata[key]
    }
  }

  private _mapLabel(nodeType: string): string {
    if (LABEL_MAP[nodeType]) return LABEL_MAP[nodeType]
    if (nodeType.startsWith('InputAction')) return nodeType
    if (nodeType.endsWith(' (Get)') || nodeType.endsWith(' (Set)')) return nodeType
    if (nodeType.includes('Unknown')) return `[Unknown] ${nodeType}`
    return nodeType
  }

  private _generateStats(graph: BlueprintGraph): Record<string, any> {
    const stats: Record<string, any> = {
      total_nodes: graph.nodes.length,
      node_type_counts: {} as Record<string, number>,
      variable_reads: 0,
      variable_writes: 0,
      function_calls: 0,
      control_flow_nodes: 0,
    }

    for (const node of graph.nodes) {
      const nt = node.node_type
      stats.node_type_counts[nt] = (stats.node_type_counts[nt] || 0) + 1

      for (const v of node.variables) {
        if (v.operation === 'read') stats.variable_reads++
        else if (v.operation === 'write') stats.variable_writes++
      }

      if (CONTROL_FLOW_TYPES.has(nt)) stats.control_flow_nodes++
      if (node.raw_type.includes('K2Node_CallFunction')) stats.function_calls++
    }

    return stats
  }
}