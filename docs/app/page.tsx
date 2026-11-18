import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen gap-6 p-8 text-center">
      <h1 className="text-4xl font-bold text-gray-900">Portalu API Docs</h1>
      <p className="text-gray-500 max-w-md">
        Everything you need to integrate with the Portalu platform.
      </p>
      <div className="flex gap-4">
        <Link
          href="/docs/guides/getting-started"
          className="px-5 py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-700"
        >
          Get Started
        </Link>
        <Link
          href="/docs/reference"
          className="px-5 py-2.5 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50"
        >
          API Reference
        </Link>
      </div>
    </main>
  )
}
