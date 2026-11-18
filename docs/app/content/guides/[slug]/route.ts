import fs from 'fs'
import path from 'path'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(_req: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const filePath = path.join(process.cwd(), 'content/guides', `${slug}.md`)
  if (!fs.existsSync(filePath)) {
    return new NextResponse('Not found', { status: 404 })
  }
  const content = fs.readFileSync(filePath, 'utf-8')
  return new NextResponse(content, {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  })
}
