import type { SchemaProperty } from '@/lib/schema'

function TypeTag({ prop }: { prop: SchemaProperty }) {
  const parts = [prop.format ?? prop.type]
  if (prop.nullable) parts.push('nullable')
  return (
    <span className="font-mono text-xs text-purple-700">{parts.join(' | ')}</span>
  )
}

function Details({ prop }: { prop: SchemaProperty }) {
  const items: React.ReactNode[] = []

  if (prop.description) {
    items.push(<span key="desc" className="block text-gray-600">{prop.description}</span>)
  }

  if (prop.enum?.length) {
    items.push(
      <span key="enum" className="block mt-1">
        {prop.enum.map(v => (
          <code key={v} className="mr-1 px-1 py-0.5 bg-gray-100 rounded text-xs">{v}</code>
        ))}
      </span>
    )
  }

  const constraints: string[] = []
  if (prop.default !== undefined) constraints.push(`default: ${JSON.stringify(prop.default)}`)
  if (prop.minLength !== undefined) constraints.push(`min length: ${prop.minLength}`)
  if (prop.maxLength !== undefined) constraints.push(`max length: ${prop.maxLength}`)
  if (prop.minimum !== undefined) constraints.push(`min: ${prop.minimum}`)
  if (prop.maximum !== undefined) constraints.push(`max: ${prop.maximum}`)
  if (prop.pattern) constraints.push(`pattern: ${prop.pattern}`)

  if (constraints.length) {
    items.push(
      <span key="constraints" className="block mt-1 text-gray-400">
        {constraints.join(' · ')}
      </span>
    )
  }

  if (!items.length) return <span className="text-gray-300">—</span>
  return <>{items}</>
}

function PropertyRow({ prop, depth }: { prop: SchemaProperty; depth: number }) {
  return (
    <>
      <tr className="border-b">
        <td className="border px-3 py-2 font-mono text-sm text-gray-900" style={{ paddingLeft: `${(depth + 1) * 12}px` }}>
          {prop.name}
          {prop.required && <span className="ml-1 text-red-500 text-xs">*</span>}
        </td>
        <td className="border px-3 py-2"><TypeTag prop={prop} /></td>
        <td className="border px-3 py-2 text-xs"><Details prop={prop} /></td>
      </tr>
      {prop.properties?.map((child) => (
        <PropertyRow key={child.name} prop={child} depth={depth + 1} />
      ))}
    </>
  )
}

export function SchemaTable({ properties }: { properties: SchemaProperty[] }) {
  if (!properties.length) return <p className="text-gray-400 text-sm italic">No properties</p>
  return (
    <div className="my-3 overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-50 text-left">
            <th className="border px-3 py-2 font-semibold text-gray-700">Field</th>
            <th className="border px-3 py-2 font-semibold text-gray-700">Type</th>
            <th className="border px-3 py-2 font-semibold text-gray-700">Details</th>
          </tr>
        </thead>
        <tbody>
          {properties.map((prop) => (
            <PropertyRow key={prop.name} prop={prop} depth={0} />
          ))}
        </tbody>
      </table>
    </div>
  )
}
