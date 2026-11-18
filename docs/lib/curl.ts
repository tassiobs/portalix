import type { SchemaProperty } from './schema'

function placeholderValue(prop: SchemaProperty): unknown {
  if (prop.enum?.length) return prop.enum[0]
  switch (prop.format) {
    case 'uuid': return '3fa85f64-5717-4562-b3fc-2c963f66afa6'
    case 'email': return 'user@example.com'
    case 'date-time': return '2024-01-01T00:00:00Z'
  }
  switch (prop.type) {
    case 'integer': return 1
    case 'number': return 1.0
    case 'boolean': return true
    case 'array': return []
    default: return prop.name === 'password' ? 'string' : `string`
  }
}

function buildExampleBody(properties: SchemaProperty[]): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  for (const prop of properties) {
    if (prop.nullable && !prop.required) continue
    body[prop.name] = placeholderValue(prop)
  }
  return body
}

export function generateCurl({
  method,
  path,
  baseUrl,
  requiresAuth,
  pathParams,
  queryParams,
  requestBodySchema,
}: {
  method: string
  path: string
  baseUrl: string
  requiresAuth: boolean
  pathParams: any[]
  queryParams: any[]
  requestBodySchema: SchemaProperty[]
}): string {
  let resolvedPath = path
  for (const p of pathParams) {
    const placeholder =
      p.schema?.format === 'uuid'
        ? '3fa85f64-5717-4562-b3fc-2c963f66afa6'
        : `{${p.name}}`
    resolvedPath = resolvedPath.replace(`{${p.name}}`, placeholder)
  }

  const queryString =
    queryParams.length > 0
      ? '?' + queryParams.map((p: any) => `${p.name}=${p.schema?.default ?? p.name}`).join('&')
      : ''

  const url = `${baseUrl}${resolvedPath}${queryString}`
  const lines: string[] = [`curl -X ${method.toUpperCase()} '${url}'`]

  if (requiresAuth) {
    lines.push(`  -H 'Authorization: Bearer <token>'`)
  }

  if (requestBodySchema.length > 0) {
    lines.push(`  -H 'Content-Type: application/json'`)
    const body = buildExampleBody(requestBodySchema)
    lines.push(`  -d '${JSON.stringify(body, null, 2)}'`)
  }

  return lines.join(' \\\n')
}
