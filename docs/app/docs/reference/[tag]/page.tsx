import { getOpenApiSpec } from '@/lib/openapi'
import { slugifyOperationId } from '@/lib/schema'
import { MethodBadge } from '@/components/MethodBadge'
import { notFound } from 'next/navigation'
import Link from 'next/link'

const tagMap: Record<string, string[]> = {
  auth: ['Auth', 'Sessions'],
  org: ['Org', 'Org Settings', 'Org Users', 'Org Roles', 'Org Permissions', 'Org Invitations'],
  portals: ['Portals', 'Portal Users', 'Request Types', 'Request Type Fields', 'Workflows', 'Portal Requests', 'Tasks', 'Task Comments'],
  requests: ['Requests'],
  citizen: ['Citizen', 'Citizen Auth', 'Citizen Request Types', 'Citizen Requests'],
}

const subgroupLabels: Record<string, string> = {
  Auth: 'Authentication',
  Sessions: 'Sessions',
  Org: 'Organization',
  'Org Settings': 'Settings',
  'Org Users': 'Users',
  'Org Roles': 'Roles',
  'Org Permissions': 'Permissions',
  'Org Invitations': 'Invitations',
  Portals: 'Portals',
  'Portal Users': 'Portal Users',
  'Request Types': 'Request Types',
  'Request Type Fields': 'Request Type Fields',
  Workflows: 'Workflows',
  'Portal Requests': 'Portal Requests',
  Tasks: 'Tasks',
  'Task Comments': 'Task Comments',
  Requests: 'Requests',
  Citizen: 'Citizen',
  'Citizen Auth': 'Authentication',
  'Citizen Request Types': 'Request Types',
  'Citizen Requests': 'Requests',
}

export async function generateStaticParams() {
  return Object.keys(tagMap).map((tag) => ({ tag }))
}

export default async function ReferenceTagPage({ params }: { params: Promise<{ tag: string }> }) {
  const { tag } = await params
  const matchedTags = tagMap[tag]
  if (!matchedTags) notFound()

  const spec = getOpenApiSpec()
  const groups: Record<string, { method: string; path: string; summary: string; operationId: string }[]> = {}

  for (const subTag of matchedTags) groups[subTag] = []

  for (const [path, methods] of Object.entries(spec.paths as Record<string, any>)) {
    for (const [method, op] of Object.entries(methods as Record<string, any>)) {
      const subTag = op.tags?.[0]
      if (subTag && groups[subTag] !== undefined) {
        groups[subTag].push({
          method,
          path,
          summary: op.summary ?? '',
          operationId: slugifyOperationId(op.operationId ?? ''),
        })
      }
    }
  }

  const hasMultipleGroups = matchedTags.length > 1

  return (
    <div>
      <h1 className="text-2xl font-bold capitalize mb-6">{tag}</h1>
      <div className="space-y-8">
        {matchedTags.map((subTag) => {
          const endpoints = groups[subTag]
          if (!endpoints.length) return null
          return (
            <section key={subTag}>
              {hasMultipleGroups && (
                <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3">
                  {subgroupLabels[subTag] ?? subTag}
                </h2>
              )}
              <div className="space-y-2">
                {endpoints.map((e) => (
                  <Link
                    key={`${e.method}-${e.path}`}
                    href={`/docs/reference/${tag}/${e.operationId}`}
                    className="flex items-start gap-3 p-3 border rounded hover:bg-gray-50 transition-colors no-underline"
                  >
                    <MethodBadge method={e.method} />
                    <div>
                      <span className="font-mono text-sm text-gray-900">{e.path}</span>
                      {e.summary && <p className="text-gray-500 text-xs mt-0.5">{e.summary}</p>}
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )
        })}
      </div>
    </div>
  )
}
