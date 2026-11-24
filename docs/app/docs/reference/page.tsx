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
    label: 'Customer',
    description: 'Public-facing portal experience — auth, request submission, and tracking for end users.',
  },
]

const errorCodes = [
  { code: '400', description: 'Invalid, expired, or already-used token (email verification, password reset).' },
  { code: '401', description: 'Missing or invalid authentication token.' },
  { code: '403', description: 'Token is valid but lacks the required permission, or account is deactivated / unverified.' },
  { code: '404', description: 'Resource not found.' },
  { code: '409', description: 'Conflict — resource already exists (duplicate email, slug already taken).' },
  { code: '422', description: 'Request body or query params failed validation. See the structured error body.' },
  { code: '423', description: 'Account locked due to too many failed login attempts.' },
]

const paginatedEndpoints = [
  'GET /api/v1/org/users',
  'GET /api/v1/org/invitations',
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
        <p className="text-gray-600 text-sm mb-4">
          Two independent token families. Each is a short-lived JWT obtained by signing in.
          Include it as a Bearer token on every authenticated request:
        </p>
        <pre className="bg-gray-900 text-gray-100 text-sm rounded-lg p-4 overflow-x-auto mb-4">
          {`Authorization: Bearer <access_token>`}
        </pre>
        <div className="border rounded-lg overflow-hidden mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Scheme</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Who</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">How to obtain</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="px-4 py-3 font-mono text-xs">StaffBearer</td>
                <td className="px-4 py-3 text-gray-600">Org staff / admins</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-600">POST /api/v1/auth/sign-in</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-xs">CustomerBearer</td>
                <td className="px-4 py-3 text-gray-600">Portal customers</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-600">POST /api/v1/customer/&#123;org_slug&#125;/&#123;portal_slug&#125;/auth/sign-in</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-gray-500 text-sm">
          Access tokens expire after 30 minutes. Use{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">/auth/refresh</code> (staff) or{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">/customer/.../auth/refresh</code> (customer) with the{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">refresh_token</code> to get a new one.
          Endpoints marked 🔓 require no token.
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
          Most list endpoints return a plain array. The following endpoints are paginated and accept{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">page</code> and{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">per_page</code> query parameters:
        </p>
        <ul className="text-sm font-mono text-gray-700 mb-4 space-y-1 pl-4 list-disc">
          {paginatedEndpoints.map(ep => <li key={ep}>{ep}</li>)}
        </ul>
        <p className="text-gray-600 text-sm mb-3">Paginated responses wrap results in a <code className="bg-gray-100 px-1 rounded text-xs">data</code> array alongside a <code className="bg-gray-100 px-1 rounded text-xs">pagination</code> object:</p>
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
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Error Codes</h2>
        <div className="border rounded-lg overflow-hidden mb-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Code</th>
                <th className="px-4 py-2 text-left font-semibold text-gray-700">Meaning</th>
              </tr>
            </thead>
            <tbody>
              {errorCodes.map((e, i) => (
                <tr key={e.code} className={i < errorCodes.length - 1 ? 'border-b' : ''}>
                  <td className="px-4 py-2"><StatusBadge code={e.code} /></td>
                  <td className="px-4 py-2 text-gray-600">{e.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-gray-600 text-sm mb-2">
          <StatusBadge code="422" /> returns a structured validation body:
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
