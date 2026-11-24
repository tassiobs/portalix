'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const nav = [
  {
    title: 'Guides',
    links: [
      { href: '/docs/guides/introduction', label: 'Introduction' },
      { href: '/docs/guides/concepts', label: 'Concepts' },
      { href: '/docs/guides/getting-started', label: 'Getting Started' },
      { href: '/docs/guides/customer-ui', label: 'Building the Customer UI' },
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
      { href: '/docs/reference/citizen', label: 'Customer' },
    ],
  },
]

export function MobileNav() {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()

  // Close drawer on navigation
  useEffect(() => { setOpen(false) }, [pathname])

  // Prevent body scroll when open
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  return (
    <>
      {/* Hamburger button */}
      <button
        onClick={() => setOpen(true)}
        className="md:hidden fixed top-4 left-4 z-40 p-2 rounded-md bg-white border border-gray-200 shadow-sm"
        aria-label="Open navigation"
      >
        <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Overlay */}
      {open && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/40"
          onClick={() => setOpen(false)}
          aria-hidden
        />
      )}

      {/* Drawer */}
      <div
        className={`md:hidden fixed top-0 left-0 z-50 h-full w-72 bg-gray-50 border-r border-gray-200 p-6 overflow-y-auto transition-transform duration-200 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between mb-8">
          <Link href="/" className="text-lg font-bold text-gray-900">
            Portalu API
          </Link>
          <button
            onClick={() => setOpen(false)}
            className="p-1 rounded text-gray-500 hover:text-gray-900"
            aria-label="Close navigation"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
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
                      className={`block text-sm py-1.5 ${
                        pathname === link.href
                          ? 'text-blue-600 font-medium'
                          : 'text-gray-700 hover:text-gray-900'
                      }`}
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </div>
    </>
  )
}
