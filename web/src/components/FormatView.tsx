import { useState, useCallback } from 'react'

interface FormatViewProps {
  text: string
  format: string
}

function FormatView({ text, format }: FormatViewProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }, [text])

  if (!text) {
    return (
      <div className="flex-1 flex flex-col bg-[#0d1117]">
        <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[#e6edf3] m-0">
            {format === 'plain' ? 'Plain Text' : format === 'markdown' ? 'Markdown' : 'Mermaid'}
          </h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-[#8b949e]">请先解析蓝图文本</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col bg-[#0d1117]">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[#e6edf3] m-0">
          {format === 'plain' ? 'Plain Text' : format === 'markdown' ? 'Markdown' : 'Mermaid'}
        </h2>
        <button
          type="button"
          onClick={handleCopy}
          className="text-xs bg-[#21262d] text-[#c9d1d9] border border-[#30363d] rounded px-3 py-1.5 hover:bg-[#30363d] hover:text-[#e6edf3] transition-colors cursor-pointer"
        >
          {copied ? '已复制' : '复制'}
        </button>
      </div>
      <div className="flex-1 overflow-auto p-4">
        <pre className="m-0 text-sm text-[#c9d1d9] font-mono whitespace-pre-wrap break-all bg-[#161b22] rounded-lg p-4 border border-[#30363d]">
          {text}
        </pre>
      </div>
    </div>
  )
}

export default FormatView