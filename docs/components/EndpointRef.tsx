const methodColors: Record<string, string> = {
  get: 'bg-blue-100 text-blue-800',
  post: 'bg-green-100 text-green-800',
  patch: 'bg-yellow-100 text-yellow-800',
  put: 'bg-orange-100 text-orange-800',
  delete: 'bg-red-100 text-red-800',
}

export function EndpointRef({
  method,
  path,
  description,
}: {
  method: string
  path: string
  description?: string
}) {
  const m = method.toLowerCase()
  return (
    <div className="flex items-start gap-3 p-3 border rounded my-2 font-mono text-sm">
      <span className={`px-2 py-0.5 rounded font-bold uppercase text-xs ${methodColors[m] ?? 'bg-gray-100 text-gray-800'}`}>
        {method}
      </span>
      <div>
        <span className="text-gray-900">{path}</span>
        {description && <p className="text-gray-500 text-xs mt-0.5 font-sans">{description}</p>}
      </div>
    </div>
  )
}
