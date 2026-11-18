const colors: Record<string, string> = {
  get: 'bg-blue-100 text-blue-800',
  post: 'bg-green-100 text-green-800',
  patch: 'bg-yellow-100 text-yellow-800',
  put: 'bg-orange-100 text-orange-800',
  delete: 'bg-red-100 text-red-800',
}

export function MethodBadge({ method }: { method: string }) {
  const m = method.toLowerCase()
  return (
    <span className={`px-2 py-0.5 rounded font-bold uppercase text-xs ${colors[m] ?? 'bg-gray-100 text-gray-800'}`}>
      {method}
    </span>
  )
}
