import { useState, useEffect, useRef, useCallback } from 'react'
import { getExamples, getExample } from '../api'

interface InputPanelProps {
  onRender: (text: string) => void
}

function InputPanel({ onRender }: InputPanelProps) {
  const [text, setText] = useState('')
  const [examples, setExamples] = useState<string[]>([])
  const [selectedExample, setSelectedExample] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    getExamples()
      .then(setExamples)
      .catch(() => {})
  }, [])

  const handleExampleChange = useCallback(async (name: string) => {
    if (!name) return
    setSelectedExample(name)
    try {
      const content = await getExample(name)
      setText(content)
    } catch {
      setSelectedExample('')
    }
  }, [])

  const handleRender = useCallback(() => {
    if (text.trim()) {
      onRender(text)
    }
  }, [text, onRender])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault()
        handleRender()
      }
    },
    [handleRender]
  )

  return (
    <aside className="w-80 shrink-0 border-r border-gray-800 bg-[#0d1117] flex flex-col">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[#e6edf3] m-0">Input</h2>
        <select
          value={selectedExample}
          onChange={(e) => handleExampleChange(e.target.value)}
          className="text-xs bg-[#21262d] text-[#c9d1d9] border border-[#30363d] rounded px-2 py-1 cursor-pointer outline-none focus:border-[#238636]"
        >
          <option value="">示例...</option>
          {examples.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>
      <div className="flex-1 p-4 flex flex-col gap-3">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="在此粘贴 UE Blueprint 文本..."
          className="flex-1 w-full bg-[#161b22] text-[#c9d1d9] border border-[#30363d] rounded-lg p-3 text-sm font-mono resize-none outline-none focus:border-[#238636] transition-colors placeholder-[#8b949e]"
        />
        <button
          type="button"
          onClick={handleRender}
          disabled={!text.trim()}
          className="w-full bg-[#238636] text-white text-sm font-medium py-2 rounded-lg hover:bg-[#2ea043] disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >
          渲染
        </button>
        <p className="text-xs text-[#8b949e] text-center">
          Ctrl + Enter 快速渲染
        </p>
      </div>
    </aside>
  )
}

export default InputPanel