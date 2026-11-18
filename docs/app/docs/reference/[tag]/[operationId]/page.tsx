import { getOpenApiSpec } from '@/lib/openapi'
import { resolveSchema, resolveRef, slugifyOperationId } from '@/lib/schema'
import { generateCurl } from '@/lib/curl'
import { MethodBadge } from '@/components/MethodBadge'
import { ParamTable } from '@/components/ParamTable'
import { SchemaTable } from '@/components/SchemaTable'
import { StatusBadge } from '@/components/StatusBadge'
import { CodeBlock } from '@/components/CodeBlock'
import { notFound } from 'next/navigation'

export async function generateStaticParams() {
  const spec = getOpenApiSpec()
  const params: { tag: string; operationId: string }[] = []

  for (const methods of Object.values(spec.paths as Record<string, any>)) {
    for (const op of Object.values(methods as Record<string, any>)) {
      if (op.operationId) {
        const tag = op.tags?.[0] ?? 'other'
        params.push({ tag: tagSlugFor(tag), operationId: slugifyOperationId(op.operationId) })
      }
    }
  }
  return params
}

function tagSlugFor(tag: string): string {
  const map: Record<string, string> = {
    Auth: 'auth',
    Sessions: 'auth',
    Org: 'org',
    'Org Settings': 'org',
    'Org Users': 'org',
    'Org Roles': 'org',
    'Org Permissions': 'org',
    'Org Invitations': 'org',
    portals: 'portals',
    Requests: 'requests',
    citizen: 'citizen',
  }
  return map[tag] ?? tag.toLowerCase()
}

export default async function EndpointPage({
  params,
}: {
  params: Promise<{ tag: string; operationId: string }>
}) {
  const { operationId } = await params
  const spec = getOpenApiSpec()
  const components = spec.components
  const baseUrl = spec.servers?.[0]?.url ?? ''

  let found: { method: string; path: string; op: any } | null = null

  for (const [path, methods] of Object.entries(spec.paths as Record<string, any>)) {
    for (const [method, op] of Object.entries(methods as Record<string, any>)) {
      if (op.operationId && slugifyOperationId(op.operationId) === operationId) {
        found = { method, path, op }
        break
      }
    }
    if (found) break
  }

  if (!found) notFound()

  const { method, path, op } = found
  const requiresAuth = !!op.security?.length

  const parameters: any[] = op.parameters ?? []
  const pathParams = parameters.filter((p: any) => p.in === 'path')
  const queryParams = parameters.filter((p: any) => p.in === 'query')

  let requestBodySchema: ReturnType<typeof resolveSchema> = []
  const requestBodyContent = op.requestBody?.content?.['application/json']?.schema
  if (requestBodyContent) {
    requestBodySchema = resolveSchema(requestBodyContent, components)
  }

  const curlExample = generateCurl({
    method,
    path,
    baseUrl,
    requiresAuth,
    pathParams,
    queryParams,
    requestBodySchema,
  })

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-3 mb-2">
        <MethodBadge method={method} />
        <code className="text-lg text-gray-800">{path}</code>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mt-2 mb-1">{op.summary}</h1>

      <div className="flex gap-3 mb-6">
        {requiresAuth ? (
          <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-800 rounded font-medium">
            🔒 Requires authentication
          </span>
        ) : (
          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">
            Public
          </span>
        )}
      </div>

      {op.description && (
        <p className="text-gray-600 mb-6">{op.description}</p>
      )}

      <section className="mb-6">
        <h2 className="text-base font-semibold text-gray-800 mb-2">Example Request</h2>
        <CodeBlock code={curlExample} language="bash" />
      </section>

      {pathParams.length > 0 && (
        <section className="mb-6">
          <h2 className="text-base font-semibold text-gray-800 mb-2">Path Parameters</h2>
          <ParamTable params={pathParams} />
        </section>
      )}

      {queryParams.length > 0 && (
        <section className="mb-6">
          <h2 className="text-base font-semibold text-gray-800 mb-2">Query Parameters</h2>
          <ParamTable params={queryParams} />
        </section>
      )}

      {requestBodySchema.length > 0 && (
        <section className="mb-6">
          <h2 className="text-base font-semibold text-gray-800 mb-2">Request Body</h2>
          {op.requestBody?.required && (
            <p className="text-xs text-red-500 mb-2">Required</p>
          )}
          <SchemaTable properties={requestBodySchema} />
        </section>
      )}

      <section className="mb-6">
        <h2 className="text-base font-semibold text-gray-800 mb-3">Responses</h2>
        <div className="space-y-4">
          {Object.entries(op.responses ?? {}).map(([code, response]: [string, any]) => {
            const schema = response.content?.['application/json']?.schema
            let resolved: ReturnType<typeof resolveSchema> = []
            if (schema) {
              const s = schema.$ref ? resolveRef(schema.$ref, components) : schema
              resolved = resolveSchema(s, components)
            }

            return (
              <div key={code} className="border rounded overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-2 bg-gray-50 border-b">
                  <StatusBadge code={code} />
                  <span className="text-sm text-gray-600">{response.description}</span>
                </div>
                {resolved.length > 0 && (
                  <div className="px-4 py-3">
                    <SchemaTable properties={resolved} />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </section>

      <section className="mb-6">
        <h2 className="text-base font-semibold text-gray-800 mb-2">Error Format</h2>
        <p className="text-sm text-gray-600 mb-2">
          Validation errors return <StatusBadge code="422" /> with the following structure:
        </p>
        <SchemaTable
          properties={resolveSchema(components.schemas.HTTPValidationError, components)}
        />
      </section>
    </div>
  )
}
