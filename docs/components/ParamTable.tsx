type Param = {
  name: string
  in: string
  required: boolean
  schema?: { type?: string; format?: string; default?: unknown; minimum?: number; maximum?: number }
  description?: string
}

export function ParamTable({ params }: { params: Param[] }) {
  if (!params.length) return null
  return (
    <div className="my-4 overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-50 text-left">
            <th className="border px-3 py-2 font-semibold text-gray-700">Name</th>
            <th className="border px-3 py-2 font-semibold text-gray-700">In</th>
            <th className="border px-3 py-2 font-semibold text-gray-700">Type</th>
            <th className="border px-3 py-2 font-semibold text-gray-700">Required</th>
            <th className="border px-3 py-2 font-semibold text-gray-700">Details</th>
          </tr>
        </thead>
        <tbody>
          {params.map((p) => {
            const details = []
            if (p.schema?.default !== undefined) details.push(`default: ${p.schema.default}`)
            if (p.schema?.minimum !== undefined) details.push(`min: ${p.schema.minimum}`)
            if (p.schema?.maximum !== undefined) details.push(`max: ${p.schema.maximum}`)
            if (p.description) details.push(p.description)
            return (
              <tr key={p.name} className="border-b">
                <td className="border px-3 py-2 font-mono text-gray-900">{p.name}</td>
                <td className="border px-3 py-2 text-gray-500">{p.in}</td>
                <td className="border px-3 py-2 text-gray-600">
                  {p.schema?.format ?? p.schema?.type ?? '—'}
                </td>
                <td className="border px-3 py-2">
                  {p.required ? (
                    <span className="text-red-600 font-medium">required</span>
                  ) : (
                    <span className="text-gray-400">optional</span>
                  )}
                </td>
                <td className="border px-3 py-2 text-gray-500 text-xs">{details.join(' · ') || '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
