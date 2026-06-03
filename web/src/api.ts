/**
 * Local blueprint engine — no server needed.
 * Parses & formats UE Blueprint text entirely in the browser.
 */

import { BlueprintParser, BlueprintTransformer, formatPlain, formatMarkdown, formatMermaid } from './engine'
import { EMBEDDED_EXAMPLES } from './engine/examples'
import type { TransformedGraph } from './types'

const parser = new BlueprintParser()
const transformer = new BlueprintTransformer()

export function parseBlueprint(text: string): TransformedGraph {
  const bpGraph = parser.parse(text)
  return transformer.transform(bpGraph)
}

export function formatBlueprint(text: string, format: 'plain' | 'markdown' | 'mermaid', _stats?: boolean): string {
  const bpGraph = parser.parse(text)
  const transformed = transformer.transform(bpGraph)

  switch (format) {
    case 'plain':
      return formatPlain(transformed, _stats ?? false)
    case 'markdown':
      return formatMarkdown(transformed, _stats ?? false)
    case 'mermaid':
      return formatMermaid(transformed, _stats ?? false)
  }
}

export function getExamples(): string[] {
  return EMBEDDED_EXAMPLES.map(e => e.name)
}

export function getExample(name: string): string {
  const example = EMBEDDED_EXAMPLES.find(e => e.name === name)
  if (!example) throw new Error(`Unknown example: ${name}`)
  return example.content
}

export { EMBEDDED_EXAMPLES }