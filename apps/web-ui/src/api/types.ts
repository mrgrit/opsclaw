export interface Project {
  id: string
  name: string
  request_text: string
  master_mode: string
  current_stage: string
  outcome?: string
  created_at: string
  updated_at?: string
}

export interface Evidence {
  id: string
  project_id: string
  command: string
  exit_code: number
  stdout: string
  stderr: string
  risk_level: string
  created_at: string
}

export interface Playbook {
  id: string
  name: string
  version: string
  description?: string
  created_at: string
}

export interface PlaybookStep {
  id: string
  playbook_id: string
  step_order: number
  step_type: string
  ref_id?: string
  params?: Record<string, unknown>
}

export interface PoWBlock {
  id: string
  agent_id: string
  project_id: string
  task_order: number
  task_title: string
  evidence_hash: string
  prev_hash: string
  block_hash: string
  nonce?: number
  difficulty?: number
  ts: string
  total_reward?: number
  base_score?: number
  speed_bonus?: number
}

export interface ReplayStep {
  task_order: number
  task_title: string
  ts: string
  block_hash: string
  exit_code: number
  duration_s: number
  risk_level: string
  total_reward: number
}

export interface Replay {
  project_id: string
  steps_total: number
  steps_success: number
  total_reward: number
  timeline: ReplayStep[]
}

export interface LedgerEntry {
  agent_id: string
  balance: number
  total_tasks: number
  success_count: number
  fail_count: number
  updated_at: string
}

export interface NotificationChannel {
  id: string
  channel_type: string
  name: string
  config: Record<string, unknown>
  created_at: string
}

export interface NotificationRule {
  id: string
  event_type: string
  channel_id: string
  created_at: string
}

export interface TaskItem {
  order: number
  title: string
  instruction_prompt: string
  risk_level: string
  subagent_url?: string
}

export interface TaskResult {
  order: number
  title: string
  status: string
  risk_level: string
  duration_s: number
  sudo_elevated?: boolean
  detail: { exit_code?: number; stdout?: string; stderr?: string; error?: string }
}

export interface ExecutePlanResult {
  status: string
  project_id: string
  tasks_total: number
  tasks_ok: number
  tasks_failed: number
  overall: string
  task_results: TaskResult[]
}

export interface DispatchResult {
  status: string
  result: {
    exit_code: number
    stdout: string
    stderr: string
    command: string
    original_command?: string
    llm_converted?: boolean
  }
}
