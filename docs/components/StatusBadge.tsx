const colors: Record<string, string> = {
  '2': 'bg-green-100 text-green-800',
  '4': 'bg-red-100 text-red-800',
  '5': 'bg-orange-100 text-orange-800',
}

export function StatusBadge({ code }: { code: string }) {
  const color = colors[code[0]] ?? 'bg-gray-100 text-gray-800'
  return (
    <span className={`px-2 py-0.5 rounded font-mono text-xs font-bold ${color}`}>{code}</span>
  )
}
