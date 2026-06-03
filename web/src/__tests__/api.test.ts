import { describe, it, expect } from 'vitest'
import { parseBlueprint, formatBlueprint, getExamples, getExample } from '../api'
import { BlueprintParser, BlueprintTransformer } from '../engine'
import type { BlueprintGraph } from '../engine/parserTypes'

// Valid blueprint sample
const SAMPLE_BLUEPRINT = `Begin Object Class=/Script/Engine.K2Node_Event Name="K2Node_Event_0"
    CustomFunctionName="EventBeginPlay"
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_1"
        PinName="then"
        PinDirection=EGPD_Output
        PinType.PinCategory="exec"
        LinkedTo=(Begin Object Class=/Script/Engine.EdGraphPin Name="pin_2"
            PinName="then"
            PinDirection=EGPD_Input
            PinType.PinCategory="exec"
        End Object)
    End Object
End Object
Begin Object Class=/Script/Engine.K2Node_CallFunction Name="K2Node_CallFunction_0"
    FunctionReference="/Script/Engine.KismetSystemLibrary.PrintString"
    Begin Object Class=/Script/Engine.EdGraphPin Name="pin_0"
        PinName="then"
        PinDirection=EGPD_Input
        PinType.PinCategory="exec"
    End Object
End Object`

describe('parseBlueprint', () => {
  it('should parse a valid blueprint synchronously', () => {
    const result = parseBlueprint(SAMPLE_BLUEPRINT)
    expect(result).toBeDefined()
    expect(result.entry_points).toBeInstanceOf(Array)
    expect(result.all_nodes).toBeDefined()
    expect(result.data_flows).toBeInstanceOf(Array)
    expect(result.stats).toBeDefined()
  })

  it('should detect entry points and execution flow', () => {
    const result = parseBlueprint(SAMPLE_BLUEPRINT)
    expect(result.entry_points.length).toBeGreaterThan(0)
    const nodeIds = Object.keys(result.all_nodes)
    expect(nodeIds.length).toBeGreaterThan(0)
  })

  it('should throw on empty text', () => {
    expect(() => parseBlueprint('')).not.toThrow()
    const result = parseBlueprint('')
    expect(result.entry_points).toEqual([])
    expect(Object.keys(result.all_nodes)).toHaveLength(0)
  })
})

describe('formatBlueprint', () => {
  it('should format as plain text', () => {
    const result = formatBlueprint(SAMPLE_BLUEPRINT, 'plain')
    expect(result).toBeTruthy()
    expect(result).toContain('[')
  })

  it('should format as markdown', () => {
    const result = formatBlueprint(SAMPLE_BLUEPRINT, 'markdown')
    expect(result).toContain('#')
  })

  it('should format as mermaid', () => {
    const result = formatBlueprint(SAMPLE_BLUEPRINT, 'mermaid')
    expect(result).toContain('```mermaid')
  })
})

describe('getExamples', () => {
  it('should return embedded example names', () => {
    const result = getExamples()
    expect(result).toContain('simple_event')
    expect(result).toContain('branch_flow')
    expect(result).toContain('variable_and_loop')
  })
})

describe('getExample', () => {
  it('should return example content', () => {
    const content = getExample('simple_event')
    expect(content).toContain('Begin Object')
  })

  it('should throw on unknown example', () => {
    expect(() => getExample('nonexistent')).toThrow('Unknown example')
  })
})

describe('BlueprintParser (low-level)', () => {
  it('should parse Begin Object / End Object blocks', () => {
    const parser = new BlueprintParser()
    const graph: BlueprintGraph = parser.parse(SAMPLE_BLUEPRINT)
    expect(graph.nodes.length).toBeGreaterThan(0)
    expect(graph.exec_flow.length).toBeGreaterThanOrEqual(0)
  })

  it('should extract pin information', () => {
    const parser = new BlueprintParser()
    const graph = parser.parse(SAMPLE_BLUEPRINT)
    for (const node of graph.nodes) {
      expect(node.pins).toBeDefined()
    }
  })
})

describe('BlueprintTransformer (low-level)', () => {
  it('should transform a parsed graph to UI structure', () => {
    const parser = new BlueprintParser()
    const transformer = new BlueprintTransformer()
    const graph = parser.parse(SAMPLE_BLUEPRINT)
    const transformed = transformer.transform(graph)
    expect(transformed.entry_points).toBeDefined()
    expect(transformed.all_nodes).toBeDefined()
    expect(typeof transformed.stats.total_nodes).toBe('number')
  })
})