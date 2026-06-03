import type { TransformedGraph, TransformedNode, PinInfo } from '../types';

const NODE_WIDTH = 200;
const HEADER_HEIGHT = 32;
const PIN_SPACING = 24;
const PIN_RADIUS = 6;
const PIN_AREA_PAD_TOP = 8;
const PIN_AREA_PAD_BOTTOM = 8;
const VAR_LINE_HEIGHT = 20;
const VAR_PADDING = 4;
const CORNER_RADIUS = 8;

const DATA_TYPE_COLORS: Record<string, string> = {
  boolean: '#ef4444',
  int: '#22d3ee',
  float: '#fbbf24',
  string: '#22c55e',
  object: '#3b82f6',
};

function getDataTypeColor(dataType: string): string {
  const lower = dataType.toLowerCase();
  return DATA_TYPE_COLORS[lower] ?? '#a78bfa';
}

function drawRoundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
): void {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function getExecPins(pins: PinInfo[], direction: string): PinInfo[] {
  return pins.filter((p) => p.pin_type === 'exec' && p.direction === direction);
}

function getDataPins(pins: PinInfo[], direction: string): PinInfo[] {
  return pins.filter((p) => p.pin_type !== 'exec' && p.direction === direction);
}

function getLeftPins(pins: PinInfo[]): PinInfo[] {
  return [...getExecPins(pins, 'input'), ...getDataPins(pins, 'input')];
}

function getRightPins(pins: PinInfo[]): PinInfo[] {
  return [...getExecPins(pins, 'output'), ...getDataPins(pins, 'output')];
}

function calcNodeHeight(node: TransformedNode): number {
  const leftCount = getLeftPins(node.pins).length;
  const rightCount = getRightPins(node.pins).length;
  const pinRows = Math.max(leftCount, rightCount, 1);
  let h = HEADER_HEIGHT + PIN_AREA_PAD_TOP + pinRows * PIN_SPACING + PIN_AREA_PAD_BOTTOM;
  if (node.variables && node.variables.length > 0) {
    h += VAR_PADDING + node.variables.length * VAR_LINE_HEIGHT + VAR_PADDING;
  }
  return h;
}

function getPinCenterY(_node: TransformedNode, pinIndex: number): number {
  return HEADER_HEIGHT + PIN_AREA_PAD_TOP + pinIndex * PIN_SPACING + PIN_SPACING / 2;
}

function getPinPosition(
  nodeId: string,
  pinName: string,
  node: TransformedNode,
  layout: Map<string, { x: number; y: number }>,
): { x: number; y: number; isOutput: boolean; isExec: boolean } | null {
  const pos = layout.get(nodeId);
  if (!pos) return null;

  const pinInfo = node.pins.find((p) => p.name === pinName);
  if (!pinInfo) return null;

  const isOutput = pinInfo.direction === 'output';
  const isExec = pinInfo.pin_type === 'exec';

  let pinIndex: number;
  if (isOutput) {
    const rightPins = getRightPins(node.pins);
    pinIndex = rightPins.findIndex((p) => p.name === pinName);
    if (pinIndex < 0) return null;
    const cx = pos.x + NODE_WIDTH;
    const cy = pos.y + getPinCenterY(node, pinIndex);
    return { x: cx, y: cy, isOutput, isExec };
  } else {
    const leftPins = getLeftPins(node.pins);
    pinIndex = leftPins.findIndex((p) => p.name === pinName);
    if (pinIndex < 0) return null;
    const cx = pos.x;
    const cy = pos.y + getPinCenterY(node, pinIndex);
    return { x: cx, y: cy, isOutput, isExec };
  }
}

function drawExecPin(ctx: CanvasRenderingContext2D, x: number, y: number, isOutput: boolean): void {
  const size = 8;
  ctx.fillStyle = '#e6edf3';
  ctx.beginPath();
  if (isOutput) {
    ctx.moveTo(x, y - size / 2);
    ctx.lineTo(x + size, y);
    ctx.lineTo(x, y + size / 2);
  } else {
    ctx.moveTo(x + size, y - size / 2);
    ctx.lineTo(x, y);
    ctx.lineTo(x + size, y + size / 2);
  }
  ctx.closePath();
  ctx.fill();
}

function drawDataPin(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  color: string,
): void {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, PIN_RADIUS, 0, Math.PI * 2);
  ctx.fill();
}

export function getNodeBounds(
  nodeId: string,
  layout: Map<string, { x: number; y: number }>,
  allNodes: Record<string, TransformedNode>,
): { x: number; y: number; width: number; height: number } | null {
  const pos = layout.get(nodeId);
  if (!pos) return null;
  const node = allNodes[nodeId];
  if (!node) return null;
  return {
    x: pos.x,
    y: pos.y,
    width: NODE_WIDTH,
    height: calcNodeHeight(node),
  };
}

export function hitTest(
  mx: number,
  my: number,
  layout: Map<string, { x: number; y: number }>,
  allNodes: Record<string, TransformedNode>,
): string | null {
  const nodeIds = Object.keys(allNodes).sort((a, b) => {
    const pa = layout.get(a);
    const pb = layout.get(b);
    if (!pa || !pb) return 0;
    return pb.y - pa.y || pb.x - pa.x;
  });

  for (const nodeId of nodeIds) {
    const bounds = getNodeBounds(nodeId, layout, allNodes);
    if (!bounds) continue;
    if (mx >= bounds.x && mx <= bounds.x + bounds.width && my >= bounds.y && my <= bounds.y + bounds.height) {
      return nodeId;
    }
  }
  return null;
}

function drawNode(ctx: CanvasRenderingContext2D, nodeId: string, node: TransformedNode, layout: Map<string, { x: number; y: number }>, selected?: boolean): void {
  const pos = layout.get(nodeId);
  if (!pos) return;

  const { x, y } = pos;
  const h = calcNodeHeight(node);
  const isUnknown = node.label.startsWith('[Unknown]');

  ctx.save();

  drawRoundRect(ctx, x, y, NODE_WIDTH, h, CORNER_RADIUS);
  ctx.fillStyle = '#1c2333';
  ctx.fill();
  ctx.strokeStyle = isUnknown ? '#636363' : '#2d3748';
  ctx.lineWidth = isUnknown ? 2 : 1;
  ctx.stroke();

  const titleGrad = ctx.createLinearGradient(x, y, x, y + HEADER_HEIGHT);
  titleGrad.addColorStop(0, '#1e40af');
  titleGrad.addColorStop(1, '#1e3a8a');
  ctx.fillStyle = titleGrad;
  drawRoundRect(ctx, x, y, NODE_WIDTH, HEADER_HEIGHT, CORNER_RADIUS);
  ctx.fill();

  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const displayLabel = node.label.length > 28 ? node.label.slice(0, 25) + '...' : node.label;
  ctx.fillText(displayLabel, x + NODE_WIDTH / 2, y + HEADER_HEIGHT / 2);

  const leftPins = getLeftPins(node.pins);
  const rightPins = getRightPins(node.pins);

  for (let i = 0; i < leftPins.length; i++) {
    const pin = leftPins[i];
    const py = y + getPinCenterY(node, i);
    const px = x;

    if (pin.pin_type === 'exec') {
      drawExecPin(ctx, px, py, false);
      ctx.fillStyle = '#8b949e';
      ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(pin.name, px + 14, py);
    } else {
      const color = getDataTypeColor(pin.pin_type);
      drawDataPin(ctx, px, py, color);
      ctx.fillStyle = '#c9d1d9';
      ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(pin.name, px + PIN_RADIUS + 6, py);
    }
  }

  for (let i = 0; i < rightPins.length; i++) {
    const pin = rightPins[i];
    const py = y + getPinCenterY(node, i);
    const px = x + NODE_WIDTH;

    if (pin.pin_type === 'exec') {
      drawExecPin(ctx, px, py, true);
      ctx.fillStyle = '#8b949e';
      ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillText(pin.name, px - 14, py);
    } else {
      const color = getDataTypeColor(pin.pin_type);
      drawDataPin(ctx, px, py, color);
      ctx.fillStyle = '#c9d1d9';
      ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillText(pin.name, px - PIN_RADIUS - 6, py);
    }
  }

  if (node.variables && node.variables.length > 0) {
    const varY = y + HEADER_HEIGHT + PIN_AREA_PAD_TOP + Math.max(leftPins.length, rightPins.length, 1) * PIN_SPACING + PIN_AREA_PAD_BOTTOM + VAR_PADDING;
    ctx.fillStyle = '#2d3748';
    ctx.fillRect(x + 4, varY - 2, NODE_WIDTH - 8, 1);
    for (let i = 0; i < node.variables.length; i++) {
      const v = node.variables[i];
      const vy = varY + 4 + i * VAR_LINE_HEIGHT;
      ctx.fillStyle = '#f0c040';
      ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      const varLabel = v.var_type ? `${v.var_type} ${v.name}` : v.name;
      const displayVar = varLabel.length > 22 ? varLabel.slice(0, 19) + '...' : varLabel;
      ctx.fillText(displayVar, x + 8, vy + VAR_LINE_HEIGHT / 2);
    }
  }

  if (selected) {
    ctx.save()
    ctx.strokeStyle = '#22c55e'
    ctx.lineWidth = 2.5
    drawRoundRect(ctx, x, y, NODE_WIDTH, h, CORNER_RADIUS)
    ctx.stroke()
    ctx.restore()
  }

  ctx.restore();
}

function drawBezierEdge(
  ctx: CanvasRenderingContext2D,
  sx: number,
  sy: number,
  tx: number,
  ty: number,
  color: string,
  lineWidth: number,
  dash: number[] | null,
): void {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  if (dash) {
    ctx.setLineDash(dash);
  }
  ctx.beginPath();
  ctx.moveTo(sx, sy);
  const cpOffset = Math.max(60, Math.abs(tx - sx) * 0.4);
  const cp1x = sx + cpOffset;
  const cp1y = sy;
  const cp2x = tx - cpOffset;
  const cp2y = ty;
  ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, tx, ty);
  ctx.stroke();
  ctx.restore();
}

function drawExecEdge(
  ctx: CanvasRenderingContext2D,
  sx: number,
  sy: number,
  tx: number,
  ty: number,
): void {
  drawBezierEdge(ctx, sx, sy, tx, ty, '#e6edf3', 2, null);
}

function drawDataEdge(
  ctx: CanvasRenderingContext2D,
  sx: number,
  sy: number,
  tx: number,
  ty: number,
  dataType: string,
): void {
  const color = getDataTypeColor(dataType);
  drawBezierEdge(ctx, sx, sy, tx, ty, color, 1.5, [5, 3]);
}

export function drawGraph(
  ctx: CanvasRenderingContext2D,
  graph: TransformedGraph,
  layout: Map<string, { x: number; y: number }>,
  selectedNodeId?: string,
): void {
  const { width, height } = ctx.canvas;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = '#0d1117';
  ctx.fillRect(0, 0, width, height);

  const drawnEdges = new Set<string>();

  for (const edge of graph.data_flows) {
    const srcNode = graph.all_nodes[edge.source_node];
    const tgtNode = graph.all_nodes[edge.target_node];
    if (!srcNode || !tgtNode) continue;

    const srcPin = getPinPosition(edge.source_node, edge.source_pin, srcNode, layout);
    const tgtPin = getPinPosition(edge.target_node, edge.target_pin, tgtNode, layout);
    if (!srcPin || !tgtPin) continue;

    const edgeKey = `${edge.source_node}:${edge.source_pin}->${edge.target_node}:${edge.target_pin}`;
    if (drawnEdges.has(edgeKey)) continue;
    drawnEdges.add(edgeKey);

    drawDataEdge(ctx, srcPin.x, srcPin.y, tgtPin.x, tgtPin.y, edge.data_type);
  }

  for (const node of Object.values(graph.all_nodes)) {
    for (const child of node.exec_children) {
      const srcPos = layout.get(node.id);
      const tgtPos = layout.get(child.id);
      if (!srcPos || !tgtPos) continue;

      const rightPins = getRightPins(node.pins);
      const execOutIndex = rightPins.findIndex((p) => p.pin_type === 'exec');
      if (execOutIndex < 0) continue;

      const leftPins = getLeftPins(child.pins);
      const execInIndex = leftPins.findIndex((p) => p.pin_type === 'exec');
      if (execInIndex < 0) continue;

      const sx = srcPos.x + NODE_WIDTH;
      const sy = srcPos.y + getPinCenterY(node, execOutIndex);

      const tx = tgtPos.x;
      const ty = tgtPos.y + getPinCenterY(child, execInIndex);

      const edgeKey = `exec:${node.id}->${child.id}`;
      if (drawnEdges.has(edgeKey)) continue;
      drawnEdges.add(edgeKey);

      drawExecEdge(ctx, sx, sy, tx, ty);
    }
  }

  const nodeIds = Object.keys(graph.all_nodes);
  nodeIds.sort((a, b) => {
    const pa = layout.get(a);
    const pb = layout.get(b);
    if (!pa || !pb) return 0;
    return pa.y - pb.y;
  });

  for (const nodeId of nodeIds) {
    const node = graph.all_nodes[nodeId];
    drawNode(ctx, nodeId, node, layout, nodeId === selectedNodeId);
  }
}