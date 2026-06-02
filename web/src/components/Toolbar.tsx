type ViewMode = 'graph' | 'plain' | 'markdown' | 'mermaid'

interface ToolbarProps {
  currentView: ViewMode
  onViewChange: (mode: ViewMode) => void
}

const views: { key: ViewMode; label: string }[] = [
  { key: 'graph', label: 'Graph' },
  { key: 'plain', label: 'Plain' },
  { key: 'markdown', label: 'Markdown' },
  { key: 'mermaid', label: 'Mermaid' },
]

function Toolbar({ currentView, onViewChange }: ToolbarProps) {
  return (
    <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-[#161b22] shrink-0">
      <h1 className="text-lg font-semibold text-[#e6edf3] m-0">
        UE Blueprint Visualizer
      </h1>
      <div className="flex items-center gap-1">
        {views.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => onViewChange(key)}
            className={`px-4 py-1.5 text-sm rounded-md transition-colors cursor-pointer ${
              currentView === key
                ? 'bg-[#238636] text-white'
                : 'bg-[#21262d] text-[#8b949e] hover:bg-[#30363d] hover:text-[#e6edf3]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </header>
  )
}

export default Toolbar
export type { ViewMode }