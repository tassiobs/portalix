import path from 'path'
import fs from 'fs'

export function getOpenApiSpec() {
  const specPath = path.join(process.cwd(), 'openapi.json')
  const raw = fs.readFileSync(specPath, 'utf-8')
  return JSON.parse(raw)
}
