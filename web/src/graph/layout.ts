import type { TransformedGraph } from '../types';

export function computeLayout(graph: TransformedGraph): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();

  const subtreeWidth = new Map<string, number>();

  function calcWidth(nodeId: string): number {
    if (subtreeWidth.has(nodeId)) return subtreeWidth.get(nodeId)!;
    const node = graph.all_nodes[nodeId];
    if (!node) return 1;
    if (node.exec_children.length === 0) {
      subtreeWidth.set(nodeId, 1);
      return 1;
    }
    let w = 0;
    for (const child of node.exec_children) {
      w += calcWidth(child.id);
    }
    subtreeWidth.set(nodeId, w);
    return w;
  }

  function assignPos(nodeIds: string[], startUnit: number, depth: number): void {
    let offset = 0;
    for (const id of nodeIds) {
      if (positions.has(id)) continue;

      const w = calcWidth(id);
      const x = (startUnit + offset + w / 2) * 250;
      const y = depth * 120;
      positions.set(id, { x, y });

      const node = graph.all_nodes[id];
      if (node && node.exec_children.length > 0) {
        const childIds = node.exec_children.map((c) => c.id);
        assignPos(childIds, startUnit + offset, depth + 1);
      }

      offset += w;
    }
  }

  const entryIds = graph.entry_points.map((ep) => ep.id);
  assignPos(entryIds, 0, 0);

  let maxY = 0;
  for (const [, pos] of positions) {
    if (pos.y > maxY) maxY = pos.y;
  }

  let orphanIndex = 0;
  for (const id of Object.keys(graph.all_nodes)) {
    if (!positions.has(id)) {
      positions.set(id, { x: orphanIndex * 250, y: maxY + 120 });
      orphanIndex++;
    }
  }

  return positions;
}