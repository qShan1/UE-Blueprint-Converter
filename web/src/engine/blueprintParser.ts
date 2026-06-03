/**
 * Recursive-descent parser for UE Blueprint text format.
 * Translates the Python parser at ue_bp_converter/parser/blueprint_parser.py
 */

import type { BlueprintGraph, NodeInfo, PinInfo, RawObject, VariableRef } from './parserTypes'

const END_OBJECT_RE = /^End\s+Object/
const BEGIN_OBJECT_RE = /^Begin\s+Object/

export class BlueprintParser {
  parse(text: string): BlueprintGraph {
    const lines = text.split('\n')
    const rawObjects = this._parseBlocks(lines, 0)[0]
    const nodes: NodeInfo[] = []
    for (const obj of rawObjects) {
      const node = this._objectToNode(obj)
      if (node) nodes.push(node)
    }
    const [execFlow, dataFlow] = this._buildConnections(nodes)
    return { nodes, exec_flow: execFlow, data_flow: dataFlow }
  }

  private _parseBlocks(lines: string[], start: number): [RawObject[], number] {
    const objects: RawObject[] = []
    let i = start
    while (i < lines.length) {
      const line = lines[i].trim()
      if (!line) { i++; continue }
      if (END_OBJECT_RE.test(line)) break
      if (BEGIN_OBJECT_RE.test(line)) {
        const [obj, nextI] = this._parseSingleObject(lines, i)
        objects.push(obj)
        i = nextI
      } else {
        i++
      }
    }
    return [objects, i]
  }

  private _parseSingleObject(lines: string[], start: number): [RawObject, number] {
    const header = lines[start].trim()
    const classMatch = header.match(/Class=(\S+)/)
    const nameMatch = header.match(/Name="([^"]*)"/)
    const classPath = classMatch ? classMatch[1] : ''
    const name = nameMatch ? nameMatch[1] : ''

    const obj: RawObject = { class_path: classPath, name, properties: {}, children: [] }
    let i = start + 1
    while (i < lines.length) {
      const line = lines[i].trim()
      if (!line) { i++; continue }
      if (END_OBJECT_RE.test(line)) { i++; break }
      if (BEGIN_OBJECT_RE.test(line)) {
        const [child, nextI] = this._parseSingleObject(lines, i)
        obj.children.push(child)
        i = nextI
        continue
      }

      const eqIdx = line.indexOf('=')
      if (eqIdx !== -1) {
        const key = line.slice(0, eqIdx).trim()
        const valueStr = line.slice(eqIdx + 1).trim()

        if (valueStr.startsWith('(Begin Object')) {
          const [innerObjs, endI] = this._parseParenBlocks(lines, i, eqIdx)
          if (innerObjs.length > 0) {
            obj.children.push(...innerObjs)
            obj.properties[key] = JSON.stringify(innerObjs)
          }
          i = endI
          continue
        }

        obj.properties[key] = this._cleanValue(valueStr)
      }
      i++
    }
    return [obj, i]
  }

  /**
   * Parse parenthesized (Begin Object ... End Object) blocks.
   * Returns the parsed objects and the index of the line AFTER the closing ).
   */
  private _parseParenBlocks(lines: string[], start: number, eqIdx: number): [RawObject[], number] {
    const firstLine = lines[start].trim()
    let parenContent = firstLine.slice(eqIdx + 1)
    if (parenContent.startsWith('(')) parenContent = parenContent.slice(1)

    const parenLines: string[] = []
    if (parenContent.trim()) parenLines.push(parenContent)

    let depth = 1
    let i = start + 1
    while (i < lines.length && depth > 0) {
      const stripped = lines[i].trim()
      const beginCount = (stripped.match(/Begin\s+Object/g) || []).length
      const endCount = (stripped.match(/End\s+Object/g) || []).length

      if (endCount > 0) {
        depth -= endCount
        if (depth <= 0) {
          i++
          break
        }
      }
      if (beginCount > 0) depth += beginCount
      parenLines.push(stripped)
      i++
    }

    const [objects] = this._parseBlocks(parenLines, 0)
    return [objects, i]
  }

  private _cleanValue(value: string): string {
    value = value.trim()
    if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1)
    if (value === 'None' || value === '') return ''
    if (value.startsWith('(') && value.endsWith(')')) {
      const inner = value.slice(1, -1).trim()
      return inner && !inner.startsWith('Begin Object') ? inner : ''
    }
    return value
  }

  private _objectToNode(obj: RawObject): NodeInfo | null {
    const { class_path: classPath, name, properties, children } = obj
    if (!classPath.includes('K2Node') && !classPath.includes('EdGraphPin')) return null
    if (classPath.includes('EdGraphPin')) return null

    const nodeType = this._deriveNodeType(classPath, properties)
    const displayName = this._deriveDisplayName(name, nodeType, properties)
    const pins = this._extractPins(children)
    const variables = this._extractVariables(nodeType, properties)

    const metadata: Record<string, string> = {}
    const skipKeys = new Set(['NodePosX', 'NodePosY', 'NodeGuid', 'bIsEnabled'])
    for (const [k, v] of Object.entries(properties)) {
      if (typeof v === 'string' && !skipKeys.has(k)) metadata[k] = v
    }

    return { name, node_type: nodeType, raw_type: classPath, display_name: displayName, pins, variables, metadata }
  }

  private _deriveNodeType(classPath: string, properties: Record<string, string>): string {
    if (classPath.includes('K2Node_Event')) return properties['CustomFunctionName'] || 'UnknownEvent'
    if (classPath.includes('K2Node_IfThenElse')) return 'Branch'
    if (classPath.includes('K2Node_CallFunction')) {
      const funcRef = (properties['FunctionReference'] || '').split('.').pop() || 'CallFunction'
      return funcRef
    }
    if (classPath.includes('K2Node_VariableGet')) return `${properties['VariableName'] || 'Unknown'} (Get)`
    if (classPath.includes('K2Node_VariableSet')) return `${properties['VariableName'] || 'Unknown'} (Set)`
    if (classPath.includes('K2Node_ForEachLoop')) return 'ForEachLoop'
    if (classPath.includes('K2Node_ForLoop')) return 'ForLoop'
    if (classPath.includes('K2Node_MathExpression')) return 'MathExpression'
    if (classPath.includes('K2Node_Select')) return 'Select'
    if (classPath.includes('K2Node_Switch')) return 'Switch'
    if (classPath.includes('K2Node_DynamicCast')) return 'DynamicCast'
    if (classPath.includes('K2Node_ExecutionSequence')) return 'ExecutionSequence'
    if (classPath.includes('K2Node_InputAction')) return `InputAction (${properties['InputActionName'] || 'UnknownAction'})`
    if (classPath.includes('K2Node_InputAxis')) return `InputAxis (${properties['InputAxisName'] || 'UnknownAxis'})`
    if (classPath.includes('K2Node_CommutativeAssociativeBinaryOperator')) return 'BinaryOperator'
    if (classPath.includes('K2Node_CustomEvent')) return properties['CustomFunctionName'] || 'CustomEvent'
    const short = classPath.includes('.') ? classPath.split('.').pop()! : classPath
    return short
  }

  private _deriveDisplayName(name: string, nodeType: string, properties: Record<string, string>): string {
    const nodeName = properties['NodeName']
    if (nodeName) return nodeName
    const category = properties['Category']
    if (category) return `${category} | ${nodeType}`
    return nodeType || name
  }

  private _extractPins(children: RawObject[]): PinInfo[] {
    const pins: PinInfo[] = []
    for (const child of children) {
      if (!child.class_path.includes('EdGraphPin')) continue  // Skip non-pin children

      const props = child.properties
      const pinName = props['PinName'] || child.name
      const rawDir = props['PinDirection'] || 'EGPD_Output'
      const direction = rawDir.includes('EGPD_Input') ? 'Input' : 'Output'
      const pinType = this._extractPinType(props)

      // LinkedTo may be JSON-stringified array of RawObjects
      const linkedToRaw = props['LinkedTo']
      let linkedTo: string[] = []
      if (linkedToRaw) {
        // The LinkedTo value is a JSON-stringified array of objects
        // Each object has properties including PinName
        try {
          const parsed = JSON.parse(linkedToRaw)
          if (Array.isArray(parsed)) {
            linkedTo = parsed.map((refObj: any) => {
              const refProps = refObj.properties || {}
              return refProps['PinName'] || refObj.name || ''
            }).filter(Boolean)
          }
        } catch {
          linkedTo = [linkedToRaw]
        }
      }

      pins.push({ name: pinName, direction, pin_type: pinType, linked_to: linkedTo })
    }
    return pins
  }

  private _extractPinType(props: Record<string, string>): string {
    return props['PinType.PinCategory'] || props['PinCategory'] || ''
  }

  private _extractVariables(nodeType: string, properties: Record<string, string>): VariableRef[] {
    const vars: VariableRef[] = []
    if (nodeType.includes('(Get)')) {
      vars.push({ name: nodeType.replace(' (Get)', ''), operation: 'read', var_type: properties['VariableType'] || null })
    } else if (nodeType.includes('(Set)')) {
      vars.push({ name: nodeType.replace(' (Set)', ''), operation: 'write', var_type: properties['VariableType'] || null })
    }
    return vars
  }

  private _buildConnections(nodes: NodeInfo[]): [BlueprintGraph['exec_flow'], BlueprintGraph['data_flow']] {
    const execFlow: BlueprintGraph['exec_flow'] = []
    const dataFlow: BlueprintGraph['data_flow'] = []

    // Build map: pin name → [(nodeName, pin), ...]
    const pinMapByName = new Map<string, [string, PinInfo][]>()
    for (const node of nodes) {
      for (const pin of node.pins) {
        if (!pinMapByName.has(pin.name)) pinMapByName.set(pin.name, [])
        pinMapByName.get(pin.name)!.push([node.name, pin])
      }
    }

    for (const node of nodes) {
      for (const pin of node.pins) {
        for (const linkedName of pin.linked_to) {
          const targets = pinMapByName.get(linkedName) || []
          for (const [tgtName, tgtPin] of targets) {
            if (tgtName === node.name) continue
            if (pin.pin_type === 'exec' && pin.direction === 'Output') {
              execFlow.push([node.name, tgtName, execFlow.length])
            } else if (pin.pin_type !== 'exec' && pin.direction === 'Output') {
              dataFlow.push([node.name, pin.name, tgtName, tgtPin.name])
            }
          }
        }
      }
    }

    // Deduplicate
    const seenExec = new Set<string>()
    const uniqueExec: BlueprintGraph['exec_flow'] = []
    for (const item of execFlow) {
      const key = `${item[0]}->${item[1]}`
      if (!seenExec.has(key)) { seenExec.add(key); uniqueExec.push(item) }
    }

    const seenData = new Set<string>()
    const uniqueData: BlueprintGraph['data_flow'] = []
    for (const item of dataFlow) {
      const key = `${item[0]}:${item[1]}->${item[2]}:${item[3]}`
      if (!seenData.has(key)) { seenData.add(key); uniqueData.push(item) }
    }

    return [uniqueExec, uniqueData]
  }
}