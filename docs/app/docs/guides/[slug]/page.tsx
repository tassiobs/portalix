import fs from 'fs'
import path from 'path'
import Markdoc from '@markdoc/markdoc'
import React from 'react'
import { Callout } from '@/components/Callout'
import { notFound } from 'next/navigation'

const components = { Callout }

export async function generateStaticParams() {
  const dir = path.join(process.cwd(), 'content/guides')
  const files = fs.readdirSync(dir)
  return files.map((f) => ({ slug: f.replace(/\.md$/, '') }))
}

export default async function GuidePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const filePath = path.join(process.cwd(), 'content/guides', `${slug}.md`)

  if (!fs.existsSync(filePath)) notFound()

  const source = fs.readFileSync(filePath, 'utf-8')
  const ast = Markdoc.parse(source)
  const content = Markdoc.transform(ast, {
    tags: {
      callout: {
        render: 'Callout',
        attributes: {
          type: { type: String, default: 'note' },
          title: { type: String },
        },
      },
    },
  })

  return <>{Markdoc.renderers.react(content, React, { components })}</>
}
