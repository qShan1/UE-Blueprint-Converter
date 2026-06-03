import { useState, useCallback } from 'react'
import Toolbar from './components/Toolbar'
import InputPanel from './components/InputPanel'
import GraphCanvas from './components/GraphCanvas'
import FormatView from './components/FormatView'
import { parseBlueprint, formatBlueprint } from './api'
import type { ViewMode } from './components/Toolbar'

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('graph')
  const [graphData, setGraphData] = useState<any>(null)
  const [formatText, setFormatText] = useState<{
    plain: string
    markdown: string
    mermaid: string
  }>({ plain: '', markdown: '', mermaid: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRender = useCallback((text: string) => {
    setLoading(true)
    setError(null)
    try {
      const parseResult = parseBlueprint(text)
      const plainText = formatBlueprint(text, 'plain', false)
      const markdownText = formatBlueprint(text, 'markdown', false)
      const mermaidText = formatBlueprint(text, 'mermaid', false)

      setGraphData(parseResult)
      setFormatText({ plain: plainText, markdown: markdownText, mermaid: mermaidText })
    } catch (err) {
      setError(err instanceof Error ? err.message : '解析失败')
      setGraphData(null)
      setFormatText({ plain: '', markdown: '', mermaid: '' })
    } finally {
      setLoading(false)
    }
  }, [])

  return (
    <div className="flex flex-col h-screen bg-[#0d1117]">
      <Toolbar currentView={viewMode} onViewChange={setViewMode} />
      <div className="flex flex-1 overflow-hidden">
        <InputPanel onRender={handleRender} />
        {loading ? (
          <div className="flex-1 flex items-center justify-center bg-[#0d1117]">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-[#238636] border-t-transparent rounded-full animate-spin" />
              <p className="text-[#8b949e] text-sm">正在解析蓝图...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center bg-[#0d1117]">
            <div className="flex flex-col items-center gap-3 max-w-md text-center px-6">
              <svg className="w-10 h-10 text-red-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <p className="text-red-400 text-sm leading-relaxed">{error}</p>
            </div>
          </div>
        ) : viewMode === 'graph' ? (
          <GraphCanvas data={graphData} />
        ) : (
          <FormatView text={formatText[viewMode]} format={viewMode} />
        )}
      </div>
    </div>
  )
}

export default App