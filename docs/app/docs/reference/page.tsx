import { getOpenApiSpec } from '@/lib/openapi'
import { StatusBadge } from '@/components/StatusBadge'
import Link from 'next/link'

const sections = [
  {
    slug: 'auth',
    label: 'Auth',
    description: 'Sign up, sign in, password management, email verification, and session control.',
  },
  {
    slug: 'org',
    label: 'Org',
    description: 'Organization profile, settings, users, roles, permissions, and invitations.',
  },
  {
    slug: 'portals',
    label: 'Portals',
    description: 'Portal configuration, request types, custom fields, workflows, requests, and tasks.',
  },
  {
    slug: 'requests',
    label: 'Requests',
    description: 'Direct org-level request management independent of a specific portal.',
  },
  {
    slug: 'citizen',
    label: 'Citizen',
    description: 'Public-facing portal experience — auth, request submission, and tracking for end users.',
  },
]

export default function ReferencePage() {
  const spec = getOpenApiSpec()
  const baseUrl = spec.servers?.[0]?.url ?? ''
  const version = spec.info.version

  return (
    <div className="max-w-3xl">
      <div className="flex items-start justify-between mb-1">
        <h1 className="text-2xl font-bold text-gray-900">API Reference</h1>
        <div className="flex flex-col items-end gap-1 mt-1">
          <a href="/openapi.json" target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
            ↗ View OpenAPI spec
          </a>
          <a href="/llms.txt" target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
            ↗ llms.txt
          </a>
        </div>
      </div>
      <p className="text-gray-500 mb-8">
        Version <strong>{version}</strong> · Base URL:{' '}
        <code className="text-sm bg-gray-100 px-1.5 py-0.5 rounded">{baseUrl}</code>
      </p>

      {/* Authentication */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Authentication</h2>
        <p className="text-gray-600 text-sm mb-3">
          Most endpoints require a Bearer token obtained by signing in. Include it in every
          authenticated request:
        </p>
        <pre className="bg-gray-900 text-gray-100 text-sm rounded-lg p-4 overflow-x-auto">
          {`Authorization: Bearer <access_token>`}
        </pre>
        <p className="text-gray-500 text-sm mt-3">
          Tokens expire — use{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">/api/v1/auth/refresh</code> with your{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">refresh_token</code> to obtain a new one.
          See <Link href="/docs/guides/getting-started" className="text-blue-600 hover:underline">Getting Started</Link> for
          a full walkthrough.
        </p>
      </section>

      {/* API Sections */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">API Sections</h2>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Section</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Description</th>
              </tr>
            </thead>
            <tbody>
              {sections.map((s, i) => (
                <tr key={s.slug} className={i < sections.length - 1 ? 'border-b' : ''}>
                  <td className="px-4 py-3">
                    <Link
                      href={`/docs/reference/${s.slug}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {s.label}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{s.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Pagination */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Pagination</h2>
        <p className="text-gray-600 text-sm mb-3">
          List endpoints that support pagination accept the following query parameters:
        </p>
        <div className="border rounded-lg overflow-hidden mb-3">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Parameter</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Type</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Default</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Description</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="px-4 py-2 font-mono">page</td>
                <td className="px-4 py-2 text-gray-500">integer</td>
                <td className="px-4 py-2 text-gray-500">1</td>
                <td className="px-4 py-2 text-gray-600">Page number (min: 1)</td>
              </tr>
              <tr>
                <td className="px-4 py-2 font-mono">per_page</td>
                <td className="px-4 py-2 text-gray-500">integer</td>
                <td className="px-4 py-2 text-gray-500">20</td>
                <td className="px-4 py-2 text-gray-600">Items per page (min: 1, max: 100)</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-gray-600 text-sm mb-2">Paginated responses include a <code className="bg-gray-100 px-1 rounded text-xs">pagination</code> object:</p>
        <pre className="bg-gray-900 text-gray-100 text-sm rounded-lg p-4 overflow-x-auto">
{`{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}`}
        </pre>
      </section>

      {/* Errors */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Error Format</h2>
        <p className="text-gray-600 text-sm mb-3">
          Validation errors return <StatusBadge code="422" /> with a structured error body:
        </p>
        <pre className="bg-gray-900 text-gray-100 text-sm rounded-lg p-4 overflow-x-auto">
{`{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}`}
        </pre>
        <p className="text-gray-500 text-sm mt-3">
          <code className="bg-gray-100 px-1 rounded text-xs">loc</code> indicates where the error
          occurred — <code className="bg-gray-100 px-1 rounded text-xs">body</code>,{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">query</code>, or{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">path</code> followed by the field name.
        </p>
      </section>
    </div>
  )
}
