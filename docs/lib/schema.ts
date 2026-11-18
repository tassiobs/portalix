export type SchemaProperty = {
  name: string
  type: string
  format?: string
  required: boolean
  default?: unknown
  description?: string
  enum?: string[]
  nullable: boolean
  minLength?: number
  maxLength?: number
  minimum?: number
  maximum?: number
  pattern?: string
  example?: unknown
  properties?: SchemaProperty[]
}

export function resolveRef(ref: string, components: any): any {
  const name = ref.replace('#/components/schemas/', '')
  return components?.schemas?.[name] ?? {}
}

export function resolveSchema(schema: any, components: any, depth = 0): SchemaProperty[] {
  if (!schema) return []

  if (schema.$ref) {
    schema = resolveRef(schema.$ref, components)
  }

  if (schema.anyOf || schema.oneOf) {
    const variants = schema.anyOf ?? schema.oneOf
    const nonNull = variants.find((v: any) => v.type !== 'null')
    if (nonNull) return resolveSchema({ ...nonNull, nullable: true }, components, depth)
    return []
  }

  if (schema.type === 'object' || schema.properties) {
    const required: string[] = schema.required ?? []
    return Object.entries(schema.properties ?? {}).map(([name, prop]: [string, any]) => {
      let resolved = prop
      if (prop.$ref) resolved = resolveRef(prop.$ref, components)

      const isNullable =
        resolved.nullable ||
        (resolved.anyOf?.some((v: any) => v.type === 'null') ?? false)

      const inner = resolved.anyOf?.find((v: any) => v.type !== 'null') ?? resolved

      return {
        name,
        type: inner.type ?? (inner.$ref ? inner.$ref.split('/').pop() : 'object'),
        format: inner.format,
        required: required.includes(name),
        default: resolved.default ?? inner.default,
        description: resolved.description ?? inner.description,
        nullable: isNullable,
        enum: inner.enum,
        minLength: inner.minLength,
        maxLength: inner.maxLength,
        minimum: inner.minimum,
        maximum: inner.maximum,
        pattern: inner.pattern,
        example: resolved.examples?.[0] ?? inner.example,
        properties:
          depth < 2 && (inner.type === 'object' || inner.properties)
            ? resolveSchema(inner, components, depth + 1)
            : undefined,
      }
    })
  }

  return []
}

export function getOperationId(method: string, path: string, op: any): string {
  return op.operationId ?? `${method}-${path}`.replace(/[^a-zA-Z0-9]/g, '-')
}

export function slugifyOperationId(operationId: string): string {
  return operationId.replace(/_/g, '-').toLowerCase()
}
