interface Props {
  stage: string
  outcome?: string
}

const stageColors: Record<string, string> = {
  created: '#6b7280',
  planning: '#3b82f6',
  planned: '#8b5cf6',
  executing: '#f59e0b',
  executed: '#10b981',
  validating: '#f59e0b',
  validated: '#10b981',
  closed: '#6b7280',
}

const outcomeColors: Record<string, string> = {
  success: '#10b981',
  failure: '#ef4444',
  partial: '#f59e0b',
}

export default function StageBadge({ stage, outcome }: Props) {
  const color = outcome ? (outcomeColors[outcome] ?? '#6b7280') : (stageColors[stage] ?? '#6b7280')
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: '9999px',
      fontSize: '0.75rem',
      fontWeight: 600,
      background: color + '22',
      color,
      border: `1px solid ${color}44`,
    }}>
      {outcome ?? stage}
    </span>
  )
}
