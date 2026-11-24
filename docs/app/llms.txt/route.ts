import fs from 'fs'
import path from 'path'
import { NextRequest, NextResponse } from 'next/server'
import { getOpenApiSpec } from '@/lib/openapi'

const GUIDE_ORDER = [
  'introduction',
  'concepts',
  'getting-started',
  'customer-ui',
  'admin-ui',
  'error-handling',
  'rbac',
]

function getGuides() {
  const dir = path.join(process.cwd(), 'content/guides')
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.md'))
  const slugs = files.map(f => f.replace(/\.md$/, ''))
  const ordered = GUIDE_ORDER.filter(s => slugs.includes(s))
  const rest = slugs.filter(s => !GUIDE_ORDER.includes(s)).sort()
  return [...ordered, ...rest]
}

function extractTitle(slug: string): string {
  const filePath = path.join(process.cwd(), 'content/guides', `${slug}.md`)
  const content = fs.readFileSync(filePath, 'utf-8')
  const match = content.match(/^#\s+(.+)$/m)
  return match ? match[1] : slug
}

function extractDescription(slug: string): string {
  const filePath = path.join(process.cwd(), 'content/guides', `${slug}.md`)
  const content = fs.readFileSync(filePath, 'utf-8')
  // Skip the title line, find the first non-empty paragraph that isn't a heading
  const lines = content.split('\n')
  let inPara = false
  const paraLines: string[] = []
  for (const line of lines) {
    if (line.startsWith('#')) { inPara = false; continue }
    if (line.startsWith('{%') || line.startsWith('---')) continue
    if (line.trim() === '') {
      if (inPara && paraLines.length > 0) break
      continue
    }
    inPara = true
    paraLines.push(line.trim())
  }
  const para = paraLines.join(' ').replace(/\*\*|`/g, '').trim()
  return para.length > 160 ? para.slice(0, 157) + '…' : para
}

export async function GET(req: NextRequest) {
  const spec = getOpenApiSpec()
  const base = new URL(req.url).origin
  const version = spec.info?.version ?? ''
  const apiBase = spec.servers?.[0]?.url ?? ''

  const guides = getGuides()
  const guideLines = guides
    .map(slug => {
      const title = extractTitle(slug)
      const desc = extractDescription(slug)
      return `- [${title}](${base}/content/guides/${slug}.md)${desc ? `: ${desc}` : ''}`
    })
    .join('\n')

  const content = `# Portalu API

> Multi-tenant platform for service-provider organisations to create customer-facing portals for request management. Orgs set up portals, define request types with custom fields and workflows; customers sign up, submit requests, and track them.

Version: ${version}
API Base URL: ${apiBase}

## Guides

${guideLines}

## API Reference

- [OpenAPI Spec](${base}/openapi.json): Full OpenAPI ${spec.openapi ?? '3.1'} specification (machine-readable)
- [Full LLM context](${base}/llms-full.txt): All guides + complete endpoint list in a single file

## Optional

- [API Reference](${base}/docs/reference): Human-readable endpoint browser
`

  return new NextResponse(content, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
