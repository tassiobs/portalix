import { CopyButton } from './CopyButton'

export function CodeBlock({ code, language = 'bash' }: { code: string; language?: string }) {
  return (
    <div className="rounded-lg overflow-hidden border border-gray-200 my-4">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
        <span className="text-xs text-gray-400 font-mono">{language}</span>
        <CopyButton text={code} />
      </div>
      <pre className="bg-gray-900 text-gray-100 p-4 overflow-x-auto text-sm font-mono leading-relaxed whitespace-pre">
        {code}
      </pre>
    </div>
  )
}
