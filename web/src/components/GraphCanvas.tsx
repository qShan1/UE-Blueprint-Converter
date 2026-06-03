import { useRef, useEffect, useState, useCallback, useMemo } from 'react'
import type { TransformedGraph } from '../types'
import { drawGraph, computeLayout, hitTest } from '../graph'

interface GraphCanvasProps {
  data: TransformedGraph | null
}

function GraphCanvas({ data }: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [scale, setScale] = useState(1)
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 })
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [nodeOffsets, setNodeOffsets] = useState<Map<string, { dx: number; dy: number }>>(new Map())

  const isDragging = useRef(false)
  const dragStart = useRef({ x: 0, y: 0 })
  const offsetAtDragStart = useRef({ x: 0, y: 0 })
  const hasAutoCentered = useRef(false)
  const isDraggingNode = useRef(false)
  const dragNodeId = useRef<string | null>(null)
  const dragNodeStart = useRef({ mx: 0, my: 0 })
  const dragNodeOffsetStart = useRef({ dx: 0, dy: 0 })

  const layout = useMemo(() => {
    if (!data) return new Map<string, { x: number; y: number }>()
    return computeLayout(data)
  }, [data])

  const renderGraph = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas || !data || layout.size === 0) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const displayWidth = canvas.clientWidth
    const displayHeight = canvas.clientHeight

    if (canvas.width !== displayWidth * dpr || canvas.height !== displayHeight * dpr) {
      canvas.width = displayWidth * dpr
      canvas.height = displayHeight * dpr
    }

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    const effectiveLayout = new Map(layout)
    for (const [id, offset] of nodeOffsets) {
      const pos = effectiveLayout.get(id)
      if (pos) {
        effectiveLayout.set(id, { x: pos.x + offset.dx, y: pos.y + offset.dy })
      }
    }

    ctx.save()
    ctx.translate(offset.x, offset.y)
    ctx.scale(scale, scale)
    drawGraph(ctx, data, effectiveLayout, selectedNodeId ?? undefined)
    ctx.restore()
  }, [data, layout, offset, scale, nodeOffsets, selectedNodeId])

  useEffect(() => {
    renderGraph()
  }, [renderGraph])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        setCanvasSize({ width, height })
      }
    })
    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!data || hasAutoCentered.current || layout.size === 0 || canvasSize.width === 0) return

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
    for (const [, pos] of layout) {
      if (pos.x < minX) minX = pos.x
      if (pos.x > maxX) maxX = pos.x
      if (pos.y < minY) minY = pos.y
      if (pos.y > maxY) maxY = pos.y
    }

    if (!isFinite(minX)) return

    const graphW = maxX - minX + 200
    const graphH = maxY - minY + 200

    const centerX = (canvasSize.width - graphW * 0.8) / 2 - minX
    const centerY = (canvasSize.height - graphH * 0.8) / 2 - minY

    setOffset({ x: centerX, y: centerY })
    hasAutoCentered.current = true
  }, [data, layout, canvasSize])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!data) return

    const canvas = canvasRef.current
    if (!canvas) return
    const canvasRect = canvas.getBoundingClientRect()
    const mx = (e.clientX - canvasRect.left - offset.x) / scale
    const my = (e.clientY - canvasRect.top - offset.y) / scale

    const effectiveLayout = new Map(layout)
    for (const [id, off] of nodeOffsets) {
      const pos = effectiveLayout.get(id)
      if (pos) {
        effectiveLayout.set(id, { x: pos.x + off.dx, y: pos.y + off.dy })
      }
    }

    const hitNodeId = hitTest(mx, my, effectiveLayout, data.all_nodes)

    if (hitNodeId) {
      setSelectedNodeId(hitNodeId)
      isDraggingNode.current = true
      dragNodeId.current = hitNodeId
      dragNodeStart.current = { mx, my }
      const curOffset = nodeOffsets.get(hitNodeId) || { dx: 0, dy: 0 }
      dragNodeOffsetStart.current = { ...curOffset }
    } else {
      setSelectedNodeId(null)
      isDragging.current = true
      dragStart.current = { x: e.clientX, y: e.clientY }
      offsetAtDragStart.current = { ...offset }
    }
  }, [data, layout, offset, scale, nodeOffsets])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDraggingNode.current && dragNodeId.current) {
      const canvas = canvasRef.current
      if (!canvas) return
      const canvasRect = canvas.getBoundingClientRect()
      const mx = (e.clientX - canvasRect.left - offset.x) / scale
      const my = (e.clientY - canvasRect.top - offset.y) / scale
      const dx = mx - dragNodeStart.current.mx
      const dy = my - dragNodeStart.current.my
      setNodeOffsets((prev) => {
        const next = new Map(prev)
        next.set(dragNodeId.current!, {
          dx: dragNodeOffsetStart.current.dx + dx,
          dy: dragNodeOffsetStart.current.dy + dy,
        })
        return next
      })
      return
    }

    if (!isDragging.current) return
    const dx = e.clientX - dragStart.current.x
    const dy = e.clientY - dragStart.current.y
    setOffset({
      x: offsetAtDragStart.current.x + dx,
      y: offsetAtDragStart.current.y + dy,
    })
  }, [offset, scale])

  const handleMouseUp = useCallback(() => {
    isDragging.current = false
    isDraggingNode.current = false
    dragNodeId.current = null
  }, [])

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setScale((prev) => {
      const newScale = Math.max(0.1, Math.min(5, prev * delta))
      return newScale
    })
  }, [])

  if (!data) {
    return (
      <div className="flex-1 flex flex-col bg-[#0d1117]">
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <svg className="w-12 h-12 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
            <p className="text-sm text-[#8b949e]">
              Blueprint graph will be rendered here
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-hidden bg-[#0d1117] relative"
      style={{ cursor: isDragging.current ? 'grabbing' : 'grab' }}
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      />
      <div className="absolute bottom-3 right-3 flex items-center gap-2 bg-[#161b22] px-3 py-1.5 rounded-md border border-gray-800 text-xs text-[#8b949e] select-none pointer-events-none">
        <span>Zoom: {Math.round(scale * 100)}%</span>
        <span className="text-gray-700">|</span>
        <span>{Object.keys(data.all_nodes).length} nodes</span>
        <span className="text-gray-700">|</span>
        <span>{data.data_flows.length} connections</span>
      </div>
      <div className="absolute top-3 left-3 flex gap-2 select-none pointer-events-none">
        <div className="flex items-center gap-1.5 text-xs text-[#8b949e] bg-[#161b22] px-2.5 py-1 rounded-md border border-gray-800">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#e6edf3]" />
          <span>Exec</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[#8b949e] bg-[#161b22] px-2.5 py-1 rounded-md border border-gray-800">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#ef4444]" />
          <span>Bool</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[#8b949e] bg-[#161b22] px-2.5 py-1 rounded-md border border-gray-800">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#22d3ee]" />
          <span>Int</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[#8b949e] bg-[#161b22] px-2.5 py-1 rounded-md border border-gray-800">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#fbbf24]" />
          <span>Float</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[#8b949e] bg-[#161b22] px-2.5 py-1 rounded-md border border-gray-800">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#22c55e]" />
          <span>Str</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[#8b949e] bg-[#161b22] px-2.5 py-1 rounded-md border border-gray-800">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#3b82f6]" />
          <span>Obj</span>
        </div>
      </div>
    </div>
  )
}

export default GraphCanvas