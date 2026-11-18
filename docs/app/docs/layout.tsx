import Link from 'next/link'

const nav = [
  {
    title: 'Guides',
    links: [
      { href: '/docs/guides/introduction', label: 'Introduction' },
      { href: '/docs/guides/concepts', label: 'Concepts' },
      { href: '/docs/guides/getting-started', label: 'Getting Started' },
      { href: '/docs/guides/citizen-ui', label: 'Building the Citizen UI' },
      { href: '/docs/guides/admin-ui', label: 'Building the Admin UI' },
      { href: '/docs/guides/error-handling', label: 'Error Handling' },
      { href: '/docs/guides/rbac', label: 'RBAC for UI' },
    ],
  },
  {
    title: 'API Reference',
    links: [
      { href: '/docs/reference', label: 'Overview' },
      { href: '/docs/reference/auth', label: 'Auth' },
      { href: '/docs/reference/org', label: 'Org' },
      { href: '/docs/reference/portals', label: 'Portals' },
      { href: '/docs/reference/requests', label: 'Requests' },
      { href: '/docs/reference/citizen', label: 'Citizen' },
    ],
  },
]

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 shrink-0 border-r border-gray-200 bg-gray-50 p-6 hidden md:block">
        <Link href="/" className="text-lg font-bold text-gray-900 mb-8 block">
          Portalu API
        </Link>
        <nav className="space-y-6">
          {nav.map((section) => (
            <div key={section.title}>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                {section.title}
              </p>
              <ul className="space-y-1">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="block text-sm text-gray-700 hover:text-gray-900 py-1"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </aside>
      <main className="flex-1 px-8 py-10 max-w-4xl prose prose-gray">
        {children}
      </main>
    </div>
  )
}
