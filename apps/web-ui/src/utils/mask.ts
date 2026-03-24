/** 시크릿(PAT, token 등)을 프론트엔드에서 이중 마스킹 */
const SECRET_PATTERNS = [
  [/ghp_[A-Za-z0-9_]{36,}/g, 'ghp_****'],
  [/github_pat_[A-Za-z0-9_]{22,}/g, 'github_pat_****'],
  [/gho_[A-Za-z0-9_]{36,}/g, 'gho_****'],
  [/ghs_[A-Za-z0-9_]{36,}/g, 'ghs_****'],
  [/glpat-[A-Za-z0-9_\-]{20,}/g, 'glpat-****'],
  [/https?:\/\/[^@\s]+@github\.com/g, 'https://****@github.com'],
] as const

export function maskSecrets(text: string): string {
  if (!text) return text
  let result = text
  for (const [pat, repl] of SECRET_PATTERNS) {
    result = result.replace(pat, repl as string)
  }
  return result
}
