/**
 * Plain, Markdown, and Mermaid formatters.
 * Translates Python formatters at ue_bp_converter/formatter/
 */

import type { TransformedGraph, TransformedNode, PinInfo } from '../types'

/* ============================================================
 * PLAIN FORMATTER
 * ============================================================ */
function formatPlain(graph: TransformedGraph, includeStats = false): string {
  const lines: string[] = []

  for (const entry of graph.entry_points) {
    lines.push(...formatNodeTreePlain(entry, 0))
  }

  if (graph.data_flows.length > 0) {
    lines.push('', '--- Data Flow ---')
    for (const df of graph.data_flows) {
      const typeInfo = df.data_type ? ` (${df.data_type})` : ''
      lines.push(`  ${df.target_node}.${df.target_pin} ← ${df.source_node}.${df.source_pin}${typeInfo}`)
    }
  }

  if (includeStats && graph.stats) {
    lines.push('', '--- Statistics ---')
    const s = graph.stats
    lines.push(`  Total Nodes: ${s.total_nodes}`)
    if (s.node_type_counts) {
      lines.push('  Node Type Counts:')
      for (const [nt, count] of Object.entries(s.node_type_counts as Record<string, number>).sort()) {
        lines.push(`    ${nt}: ${count}`)
      }
    }
    lines.push(`  Variable Reads: ${s.variable_reads}`)
    lines.push(`  Variable Writes: ${s.variable_writes}`)
    lines.push(`  Function Calls: ${s.function_calls}`)
    lines.push(`  Control Flow Nodes: ${s.control_flow_nodes}`)
  }

  return lines.join('\n')
}

function formatNodeTreePlain(node: TransformedNode, depth: number): string[] {
  const lines: string[] = []
  const indent = '  '.repeat(depth)

  const dataPinStr = formatDataPins(node)
  let line = `${indent}[${node.label}]`
  if (dataPinStr) line += `  (${dataPinStr})`
  lines.push(line)

  const children = node.exec_children
  if (children.length === 0) return lines

  const execOutPins = (node.pins as PinInfo[]).filter(p => p.direction === 'Output' && p.pin_type === 'exec')

  for (let i = 0; i < children.length; i++) {
    const child = children[i]
    const isLast = i === children.length - 1
    const childIndent = '  '.repeat(depth + 1)

    let connector: string
    let pinLabel: string
    if (children.length === 1) {
      connector = '→ '
      pinLabel = ''
    } else {
      connector = isLast ? '└─ ' : '├─ '
      pinLabel = ''
      if (i < execOutPins.length) {
        const raw = execOutPins[i].name
        pinLabel = raw[0].toUpperCase() + raw.slice(1) + ' → '
      }
    }

    const childLines = formatNodeTreePlain(child, depth + 1)
    const childHeader = childLines[0].trimStart()
    childLines[0] = `${childIndent}${connector}${pinLabel}${childHeader}`
    lines.push(...childLines)
  }

  return lines
}

function formatDataPins(node: TransformedNode): string {
  const dataPins = (node.pins as PinInfo[]).filter(p => p.direction === 'Input' && p.pin_type !== 'exec')
  return dataPins.map(p => p.pin_type ? `${p.name}: ${p.pin_type}` : p.name).join(', ')
}

/* ============================================================
 * MARKDOWN FORMATTER
 * ============================================================ */
function formatMarkdown(graph: TransformedGraph, includeStats = false): string {
  const sections: string[] = ['# Blueprint Analysis', '']

  sections.push(formatNodeSummary(graph), '')
  sections.push(formatExecFlowMd(graph), '')

  if (graph.data_flows.length > 0) {
    sections.push(formatDataFlowMd(graph), '')
  }

  if (includeStats && graph.stats) {
    sections.push(formatStatsMd(graph))
  }

  return sections.join('\n').replace(/\n+$/, '') + '\n'
}

function formatNodeSummary(graph: TransformedGraph): string {
  const lines = ['## Node Summary', '', '| ID | Label | Type | Pins |', '|---|------|------|------|']
  const sortedIds = Object.keys(graph.all_nodes).sort((a, b) => {
    const na = parseInt(a.split('_')[1])
    const nb = parseInt(b.split('_')[1])
    return na - nb
  })
  for (const nid of sortedIds) {
    const node = graph.all_nodes[nid]
    const pinDesc = (node.pins as PinInfo[]).map(p => {
      if (p.pin_type === 'exec') return `${p.name}(exec)`
      const typeStr = p.pin_type ? `:${p.pin_type}` : ''
      return `${p.name}(${p.direction.toLowerCase()}${typeStr})`
    }).join(', ')
    lines.push(`| ${nid} | ${node.label} | ${node.node_type} | ${pinDesc} |`)
  }
  return lines.join('\n')
}

function formatExecFlowMd(graph: TransformedGraph): string {
  const lines = ['## Execution Flow', '']
  let counter = 1
  for (let i = 0; i < graph.entry_points.length; i++) {
    lines.push(...formatExecNodeMd(graph.entry_points[i], 0, () => counter++, i === graph.entry_points.length - 1))
  }
  return lines.join('\n')
}

function formatExecNodeMd(node: TransformedNode, depth: number, nextNum: () => number, _isLastSibling: boolean): string[] {
  const lines: string[] = []
  const indent = '  '.repeat(depth)

  if (depth === 0) {
    lines.push(`${indent}${nextNum()}. **${node.label}** (${node.id})`)
  } else {
    lines.push(`${indent}- → **${node.label}** (${node.id})`)
  }

  for (let i = 0; i < node.exec_children.length; i++) {
    lines.push(...formatExecNodeMd(node.exec_children[i], depth + 1, nextNum, i === node.exec_children.length - 1))
  }

  return lines
}

function formatDataFlowMd(graph: TransformedGraph): string {
  const lines = ['## Data Flow', '', '| From | Pin | → | To | Pin | Type |', '|------|-----|---|----|-----|------|']
  for (const df of graph.data_flows) {
    lines.push(`| ${df.source_node} | ${df.source_pin} | → | ${df.target_node} | ${df.target_pin} | ${df.data_type} |`)
  }
  return lines.join('\n')
}

function formatStatsMd(graph: TransformedGraph): string {
  const lines = ['## Statistics', '']
  const s = graph.stats
  lines.push(`- **Total Nodes**: ${s.total_nodes}`)
  lines.push(`- **Variable Reads**: ${s.variable_reads}`)
  lines.push(`- **Variable Writes**: ${s.variable_writes}`)
  lines.push(`- **Function Calls**: ${s.function_calls}`)
  lines.push(`- **Control Flow Nodes**: ${s.control_flow_nodes}`)

  const ntc = s.node_type_counts as Record<string, number> | undefined
  if (ntc && Object.keys(ntc).length > 0) {
    lines.push('- **Node Type Counts**:')
    for (const [nt, count] of Object.entries(ntc).sort()) {
      lines.push(`  - ${nt}: ${count}`)
    }
  }
  return lines.join('\n')
}

/* ============================================================
 * MERMAID FORMATTER
 * ============================================================ */
function formatMermaid(graph: TransformedGraph, includeStats = false): string {
  const lines: string[] = ['```mermaid', 'flowchart TD', '']

  const sortedIds = Object.keys(graph.all_nodes).sort((a, b) => {
    const na = parseInt(a.split('_')[1])
    const nb = parseInt(b.split('_')[1])
    return na - nb
  })
  for (const nid of sortedIds) {
    const node = graph.all_nodes[nid]
    const escaped = node.label.replace(/"/g, '#quot;')
    lines.push(`    ${nid}["${escaped}"]`)
  }

  lines.push('')

  for (const entry of graph.entry_points) {
    collectExecEdges(entry, graph, lines)
  }

  if (graph.data_flows.length > 0) {
    lines.push('')
    for (const df of graph.data_flows) {
      const escaped = df.source_pin.replace(/"/g, '#quot;')
      lines.push(`    ${df.source_node} -.->|"${escaped}"| ${df.target_node}`)
    }
  }

  if (includeStats && graph.stats) {
    const s = graph.stats
    lines.push('', `    %% Total Nodes: ${s.total_nodes}`, `    %% Variable Reads: ${s.variable_reads}`, `    %% Variable Writes: ${s.variable_writes}`, `    %% Function Calls: ${s.function_calls}`, `    %% Control Flow Nodes: ${s.control_flow_nodes}`)
  }

  lines.push('```')
  return lines.join('\n') + '\n'
}

function collectExecEdges(node: TransformedNode, graph: TransformedGraph, lines: string[]): void {
  const execOutPins = (node.pins as PinInfo[]).filter(p => p.direction === 'Output' && p.pin_type === 'exec')
  for (let i = 0; i < node.exec_children.length; i++) {
    const child = node.exec_children[i]
    let label = ''
    if (i < execOutPins.length) {
      const raw = execOutPins[i].name
      label = raw[0].toUpperCase() + raw.slice(1)
    }
    if (label) {
      const escaped = label.replace(/"/g, '#quot;')
      lines.push(`    ${node.id} -->|"${escaped}"| ${child.id}`)
    } else {
      lines.push(`    ${node.id} --> ${child.id}`)
    }
    collectExecEdges(child, graph, lines)
  }
}

/* ============================================================
 * EXPORTS
 * ============================================================ */
export { formatPlain, formatMarkdown, formatMermaid }