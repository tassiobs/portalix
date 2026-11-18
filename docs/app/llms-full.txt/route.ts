import fs from 'fs'
import path from 'path'
import { NextResponse } from 'next/server'
import { getOpenApiSpec } from '@/lib/openapi'

function readGuide(slug: string): string {
  const filePath = path.join(process.cwd(), 'content/guides', `${slug}.md`)
  return fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf-8') : ''
}

function endpointSummary(spec: ReturnType<typeof getOpenApiSpec>): string {
  const lines: string[] = []
  const tagOrder = [
    'Auth', 'Sessions',
    'Org', 'Org Settings', 'Org Users', 'Org Roles', 'Org Permissions', 'Org Invitations',
    'Portals', 'Portal Users', 'Request Types', 'Request Type Fields', 'Workflows', 'Portal Requests', 'Tasks', 'Task Comments',
    'Requests',
    'Citizen', 'Citizen Auth', 'Citizen Request Types', 'Citizen Requests',
  ]

  const byTag: Record<string, { method: string; path: string; summary: string }[]> = {}
  for (const [pathStr, methods] of Object.entries(spec.paths ?? {})) {
    for (const [method, op] of Object.entries(methods as Record<string, { tags?: string[]; summary?: string }>)) {
      if (!['get', 'post', 'put', 'patch', 'delete'].includes(method)) continue
      const tag = op.tags?.[0] ?? 'Other'
      if (!byTag[tag]) byTag[tag] = []
      byTag[tag].push({ method: method.toUpperCase(), path: pathStr, summary: op.summary ?? '' })
    }
  }

  const orderedTags = [...tagOrder.filter(t => byTag[t]), ...Object.keys(byTag).filter(t => !tagOrder.includes(t))]

  for (const tag of orderedTags) {
    lines.push(`\n### ${tag}\n`)
    for (const op of byTag[tag]) {
      const summary = op.summary ? ` — ${op.summary}` : ''
      lines.push(`- ${op.method} ${op.path}${summary}`)
    }
  }

  return lines.join('\n')
}

export async function GET() {
  const spec = getOpenApiSpec()
  const apiBase = spec.servers?.[0]?.url ?? 'https://portalu-production.up.railway.app'
  const version = spec.info?.version ?? ''

  const guideOrder = ['introduction', 'concepts', 'getting-started', 'citizen-ui', 'admin-ui', 'error-handling', 'rbac']
  const guideDir = path.join(process.cwd(), 'content/guides')
  const allSlugs = fs.readdirSync(guideDir).filter(f => f.endsWith('.md')).map(f => f.replace(/\.md$/, ''))
  const ordered = guideOrder.filter(s => allSlugs.includes(s))
  const rest = allSlugs.filter(s => !guideOrder.includes(s)).sort()
  const guides = [...ordered, ...rest]

  const guideSections = guides
    .map(slug => readGuide(slug))
    .filter(Boolean)
    .join('\n\n---\n\n')

  const content = `# Portalu API — Full LLM Context

> Multi-tenant platform for service-provider organisations to create citizen-facing portals for request management.

Version: ${version}
Base URL: ${apiBase}
OpenAPI spec: ${apiBase}/openapi.json

---

## Authentication

Two separate auth systems:

**Org Users** (internal staff) — authenticate via \`/api/v1/auth/*\`. Receive a JWT access token and refresh token. Include access token as \`Authorization: Bearer <token>\` on all requests.

**Citizens** (end users) — authenticate via \`/api/v1/citizen/{org_slug}/{portal_slug}/auth/*\`. Same token model, scoped to a specific portal.

Access tokens expire. Use the \`/refresh\` endpoint with the refresh token to get a new one.

---

${guideSections}

---

## All Endpoints
${endpointSummary(spec)}
`

  return new NextResponse(content, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
