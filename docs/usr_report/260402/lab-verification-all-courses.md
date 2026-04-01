# 전 과목 교안 실습 검증 보고서 (2026-04-02)

## 검증 범위
- 10개 과목 × 3주차(W01, W08, W15) = 30개 핵심 실습 테스트
- 실제 시스템에서 명령 실행하여 PASS/FAIL 판정

## 결과: 30/30 ALL PASS ✅

### Course 1-5 (공격/방어/웹/컴플라이언스/SOC)

| Course | W01 | W08 | W15 | Issues |
|--------|-----|-----|-----|--------|
| C1 Attack | ✅ nmap scan | ✅ CTF API | ✅ SQLi test | W15 URL 수정 |
| C2 Security Ops | ✅ nftables | ✅ Suricata | ✅ Wazuh | - |
| C3 Web Vuln | ✅ HTTP headers | ✅ SQLi login | ✅ Product search | - |
| C4 Compliance | ✅ SSH config | ✅ Password policy | ✅ Service count | $srv 변수 수정 |
| C5 SOC | ✅ Wazuh status | ✅ auth.log | ✅ Blue Team env | - |

### Course 6-10 (클라우드/AI보안/Safety/자율/에이전트)

| Course | W01 | W08 | W15 | Issues |
|--------|-----|-----|-----|--------|
| C6 Cloud/Container | ✅ docker ps | ✅ docker inspect | ✅ OpsClaw dispatch | - |
| C7 AI Security | ✅ Ollama models | ✅ OpsClaw lifecycle | ✅ execute-plan | - |
| C8 AI Safety | ✅ Prompt injection | ✅ Jailbreak test | ✅ Model listing | - |
| C9 Autonomous | ✅ API health | ✅ CTF execute-plan | ✅ PoW+RL verify | - |
| C10 AI Agent | ✅ Ollama chat | ✅ Security scan | ✅ Full lifecycle | - |

## 수정 사항
1. course1-attack/week15: `/rest/products/1` → `/rest/products/search?q=test` (JuiceShop v17 호환)
2. course4-compliance/week08,15: `$srv` 변수 매핑 추가 (`case $ip in ... esac`)

## 검증 환경
- v-secu(192.168.0.108): nftables ✅, Suricata ✅
- v-web(192.168.0.110): Apache ✅, Docker ✅, JuiceShop ✅
- v-siem(192.168.0.109): Wazuh Manager ✅
- Ollama(192.168.0.105): 22 models ✅
- OpsClaw: Manager/Master/SubAgent 전부 정상
- PoW: 284 blocks, valid=true
- RL: 48 states, Q-table populated
