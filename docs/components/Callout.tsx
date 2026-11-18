type CalloutType = 'note' | 'warning' | 'error' | 'tip'

const styles: Record<CalloutType, string> = {
  note: 'bg-blue-50 border-blue-400 text-blue-900',
  warning: 'bg-yellow-50 border-yellow-400 text-yellow-900',
  error: 'bg-red-50 border-red-400 text-red-900',
  tip: 'bg-green-50 border-green-400 text-green-900',
}

export function Callout({
  type = 'note',
  title,
  children,
}: {
  type?: CalloutType
  title?: string
  children: React.ReactNode
}) {
  return (
    <div className={`border-l-4 p-4 my-4 rounded-r ${styles[type]}`}>
      {title && <p className="font-semibold mb-1">{title}</p>}
      <div>{children}</div>
    </div>
  )
}
