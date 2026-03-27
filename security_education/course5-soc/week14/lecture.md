# Week 14: 자동화 관제 - OpsClaw Agent Daemon

## 학습 목표

- OpsClaw의 자율 보안 관제 아키텍처를 이해한다
- Agent Daemon의 explore/daemon/stimulate 모드를 실습한다
- AI 기반 자동 탐지→분석→대응 흐름을 확인한다
- 자동화 관제의 장점과 한계를 토론한다

---

## 1. 왜 자동화 관제가 필요한가?

### 1.1 수동 관제의 한계

| 문제 | 설명 |
|------|------|
| 경보 피로 | 하루 수백~수천 건의 경보를 사람이 분석 |
| 24/7 운영 | SOC 분석원의 야간/주말 근무 부담 |
| 일관성 | 분석원마다 판단이 다름 |
| 대응 속도 | 탐지→분석→대응에 수 시간 소요 |
| 인력 부족 | 보안 인력 수급난 |

### 1.2 자동화의 목표

```
기존: [경보] → [분석원 확인] → [수동 분석] → [수동 대응]
자동: [경보] → [AI 자동 분석] → [자동 격리/대응] → [분석원 검토]
```

---

## 2. OpsClaw Agent Daemon 아키텍처

### 2.1 구성 요소

```
[Claude Code / Master]
        ↓ (오케스트레이션)
[Manager API :8000]
        ↓ (태스크 분배)
[SubAgent :8002] ← 각 서버에서 실행
        ↓
[실행 결과 + PoW 블록]
```

### 2.2 Agent Daemon 3가지 모드

| 모드 | 목적 | 동작 |
|------|------|------|
| explore | 환경 탐색 | 서버 상태, 서비스, 설정 수집 |
| daemon | 상시 감시 | 로그 모니터링, 이상 탐지 |
| stimulate | 자극 테스트 | 모의 공격으로 탐지 체계 검증 |

### 2.3 실습 환경

```
Manager API: http://localhost:8000
SubAgent: http://localhost:8002 (opsclaw)
          http://192.168.208.150:8002 (secu)
          http://192.168.208.151:8002 (web)
          http://192.168.208.152:8002 (siem)
API Key: opsclaw-api-key-2026
```

---

## 3. Explore 모드: 환경 탐색

### 3.1 프로젝트 생성 및 탐색

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 1. 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"explore-lab","request_text":"실습 환경 탐색","master_mode":"external"}' | python3 -m json.tool

# 프로젝트 ID 확인
PROJECT_ID=$(curl -s http://localhost:8000/projects -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "import sys,json; ps=json.load(sys.stdin); print(ps[-1]['id'])" 2>/dev/null)
echo "Project ID: $PROJECT_ID"
```

### 3.2 환경 탐색 태스크 실행

```bash
# stage 전환
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" -H "X-API-Key: $OPSCLAW_API_KEY"

# 탐색 태스크 실행
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"hostname && uname -a && uptime", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":2, "instruction_prompt":"ss -tlnp | grep LISTEN", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":3, "instruction_prompt":"systemctl list-units --type=service --state=running --no-pager | head -20", "risk_level":"low", "subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -m json.tool
```

### 3.3 결과 확인

```bash
# 실행 결과 확인
curl -s "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

---

## 4. Daemon 모드: 상시 감시

### 4.1 감시 태스크 예시

```bash
# 새 프로젝트 생성 (daemon)
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"daemon-monitor","request_text":"상시 보안 감시","master_mode":"external"}' | python3 -m json.tool

DAEMON_ID=$(curl -s http://localhost:8000/projects -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "import sys,json; ps=json.load(sys.stdin); print(ps[-1]['id'])" 2>/dev/null)

curl -s -X POST "http://localhost:8000/projects/$DAEMON_ID/plan" -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$DAEMON_ID/execute" -H "X-API-Key: $OPSCLAW_API_KEY"

# 보안 감시 태스크
curl -s -X POST "http://localhost:8000/projects/$DAEMON_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"grep -c \"Failed password\" /var/log/auth.log 2>/dev/null || echo 0", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":2, "instruction_prompt":"ss -tnp state established | grep -v \"192.168\\|10.20\\|127.0\" | wc -l", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":3, "instruction_prompt":"find /tmp -type f -executable 2>/dev/null | wc -l", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":4, "instruction_prompt":"ps aux --sort=-%cpu | head -5", "risk_level":"low", "subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -m json.tool
```

### 4.2 다중 서버 감시

```bash
# secu 서버 감시
curl -s -X POST "http://localhost:8000/projects/$DAEMON_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"tail -5 /var/log/suricata/fast.log 2>/dev/null || echo No alerts","subagent_url":"http://192.168.208.150:8002"}' | python3 -m json.tool

# siem 서버 감시
curl -s -X POST "http://localhost:8000/projects/$DAEMON_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"systemctl is-active wazuh-manager 2>/dev/null","subagent_url":"http://192.168.208.152:8002"}' | python3 -m json.tool
```

---

## 5. Stimulate 모드: 자극 테스트

### 5.1 Purple Team 개념

```
Red Team (공격)  +  Blue Team (방어)  =  Purple Team (협력)
```

Stimulate 모드는 **안전한 모의 공격**으로 탐지 체계를 검증한다.

### 5.2 탐지 체계 테스트

```bash
# 새 프로젝트 (stimulate)
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"stimulate-test","request_text":"탐지 체계 검증","master_mode":"external"}' | python3 -m json.tool

STIM_ID=$(curl -s http://localhost:8000/projects -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "import sys,json; ps=json.load(sys.stdin); print(ps[-1]['id'])" 2>/dev/null)

curl -s -X POST "http://localhost:8000/projects/$STIM_ID/plan" -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$STIM_ID/execute" -H "X-API-Key: $OPSCLAW_API_KEY"

# 안전한 테스트 태스크
curl -s -X POST "http://localhost:8000/projects/$STIM_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"echo \"Test: SSH failure detection\" && logger -p auth.warning \"Failed password for testuser from 10.99.99.99 port 22 ssh2\"", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":2, "instruction_prompt":"echo \"Test: Check if Wazuh detected the test event\" && sleep 5 && tail -3 /var/log/auth.log", "risk_level":"low", "subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -m json.tool
```

---

## 6. PoW (Proof of Work) 확인

### 6.1 작업 증명 블록 조회

```bash
# PoW 블록 확인
curl -s "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool | head -30

# 체인 무결성 검증
curl -s "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# 리더보드 (SubAgent별 작업량)
curl -s "http://localhost:8000/pow/leaderboard" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

### 6.2 작업 Replay

```bash
# 프로젝트 작업 기록 재생
curl -s "http://localhost:8000/projects/$DAEMON_ID/replay" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

---

## 7. 자동화 관제의 장단점

### 7.1 장점

| 장점 | 설명 |
|------|------|
| 속도 | 초 단위 탐지→대응 가능 |
| 일관성 | 항상 동일한 기준으로 판단 |
| 확장성 | 서버 수 증가에도 동일 비용 |
| 24/7 | 사람 없이 상시 운영 |
| 기록 | 모든 판단과 조치가 PoW로 기록 |

### 7.2 한계

| 한계 | 설명 |
|------|------|
| 오탐 대응 | AI도 FP를 생성할 수 있음 |
| 맥락 이해 | 비즈니스 맥락은 사람이 판단 |
| 새로운 공격 | 학습 데이터에 없는 공격은 미탐 가능 |
| 책임 | 자동 조치의 책임 소재 불명확 |
| 신뢰 | 자동 차단이 정상 트래픽을 막을 위험 |

### 7.3 권장 접근법

```
Level 1: 자동 탐지 + 사람 분석 (현재 대부분의 SOC)
Level 2: 자동 탐지 + 자동 분석 + 사람 승인 → 자동 대응
Level 3: 자동 탐지 + 자동 분석 + 자동 대응 (low risk만)
         + 사람 감독 (high risk)
```

---

## 8. 실습: 자동화 관제 워크플로우

### 8.1 전체 흐름

```bash
echo "============================================"
echo " 자동화 관제 데모"
echo "============================================"

export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 1. 환경 탐색
echo "[1] 환경 탐색"
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"auto-soc-demo","request_text":"자동화 관제 데모","master_mode":"external"}' 2>/dev/null | python3 -c "import sys,json; print(f'Project: {json.load(sys.stdin).get(\"id\",\"?\")}')" 2>/dev/null

# 2. 결과 확인
echo ""
echo "[2] 프로젝트 목록"
curl -s http://localhost:8000/projects \
  -H "X-API-Key: $OPSCLAW_API_KEY" 2>/dev/null | python3 -c "
import sys,json
ps = json.load(sys.stdin)
for p in ps[-3:]:
    print(f'  {p[\"id\"]}: {p[\"name\"]} ({p[\"stage\"]})')
" 2>/dev/null

# 3. PoW 리더보드
echo ""
echo "[3] 작업 증명 리더보드"
curl -s http://localhost:8000/pow/leaderboard \
  -H "X-API-Key: $OPSCLAW_API_KEY" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -15
```

---

## 9. 핵심 정리

1. **자동화 관제** = AI가 탐지→분석→대응을 자동 수행
2. **OpsClaw** = Manager API를 통한 중앙 오케스트레이션
3. **3가지 모드** = explore(탐색), daemon(감시), stimulate(테스트)
4. **PoW** = 모든 작업이 블록체인으로 기록/검증
5. **인간 감독** = 자동화의 한계를 보완하는 사람의 역할

---

## 과제

1. OpsClaw API를 사용하여 4개 서버의 보안 상태를 탐색(explore)하시오
2. daemon 모드 태스크를 설계하여 주요 보안 지표를 수집하시오
3. 자동화 관제의 장단점을 비교하고, 우리 환경에서의 최적 적용 방안을 제안하시오

---

## 참고 자료

- OpsClaw API Guide: docs/api/external-master-guide.md
- SOAR(Security Orchestration, Automation and Response) 개요
- AI in SOC: Benefits and Challenges
