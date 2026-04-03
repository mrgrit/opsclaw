# Week 14: 대규모 공방전 — 다대다 팀전, Attack/Defense CTF 운영

## 학습 목표
- Attack/Defense CTF의 규칙과 운영 구조를 이해한다
- 다대다(Multi-team) 공방전 환경을 설계하고 구성할 수 있다
- 팀 기반 공격/방어 전략을 수립하고 실행할 수 있다
- 실시간 스코어보드와 판정 시스템을 이해한다
- OpsClaw를 CTF 플랫폼으로 활용한 대규모 공방전을 운영할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 01-13 전체 내용 이해
- 팀 리더십 및 커뮤니케이션

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | CTF 관리 서버 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 네트워크 인프라 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 경기장 서버 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | 모니터링/판정 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | A/D CTF 이론 및 규칙 | 강의 |
| 0:30-1:00 | 팀 편성 및 전략 수립 | 토론 |
| 1:00-1:10 | 휴식 | - |
| 1:10-2:30 | 대규모 공방전 실전 (80분) | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 결과 분석 및 디브리핑 | 토론 |
| 3:10-3:30 | 운영 노하우 공유 + 퀴즈 | 토론 |

---

# Part 1: Attack/Defense CTF 이론 (30분)

## 1.1 CTF 유형 비교

| 유형 | 형식 | 난이도 | 팀워크 |
|------|------|--------|--------|
| Jeopardy | 문제 풀이 | 중 | 낮음 |
| Attack/Defense | 실시간 공방 | 상 | 높음 |
| King of the Hill | 서버 점령 | 중상 | 중 |
| Red vs Blue | 역할 고정 | 상 | 높음 |

## 1.2 A/D CTF 규칙 구조

```
┌─────────────────────────────────────────────┐
│                 Game Server                  │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐   │
│  │Team A│  │Team B│  │Team C│  │Team D│   │
│  │서버   │  │서버   │  │서버   │  │서버   │   │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘   │
│     └─────────┼─────────┼─────────┘        │
│               │                             │
│         [Score Board]                       │
│    Flag 점수 + SLA 점수 + 방어 점수          │
└─────────────────────────────────────────────┘
```

## 1.3 점수 체계

| 항목 | 점수 | 조건 |
|------|------|------|
| Flag 획득 | +100 | 상대 서버에서 flag 탈취 |
| 서비스 가용성 (SLA) | +50/라운드 | 서비스 정상 응답 |
| 방어 성공 | +30 | 공격 시도 차단 |
| 서비스 다운 | -50 | 자기 서비스 장애 |
| 자가 Flag 노출 | -100 | 본인 flag 유출 |

---

# Part 2: 팀 편성 및 전략 수립 (30분)

## 2.1 팀 역할 분담

```markdown
## Team Structure (4명 기준)
1. **Attack Leader**: 공격 전략 수립, 익스플로잇 조율
2. **Defense Leader**: 방어 규칙 관리, 패치 적용
3. **Intel/Recon**: 정보 수집, 취약점 분석
4. **Infra/SLA**: 서비스 가용성 유지, 모니터링
```

## 2.2 전략 수립 워크시트

```markdown
## Pre-Game Checklist
### 방어 (우선 실행)
- [ ] 초기 서버 백업
- [ ] 불필요 서비스 비활성화
- [ ] 기본 비밀번호 변경
- [ ] 방화벽 규칙 설정 (최소 허용)
- [ ] 로그 모니터링 활성화
- [ ] Flag 파일 권한 설정

### 공격 (방어 안정화 후)
- [ ] 상대 서버 포트 스캔
- [ ] 웹 서비스 취약점 탐색
- [ ] 자동 익스플로잇 스크립트 준비
- [ ] Flag 제출 자동화
```

---

# Part 3: 대규모 공방전 실전 (80분)

## 실습 3.1: 환경 초기화

> **목적**: CTF 경기장을 구성한다
> **배우는 것**: CTF 인프라 운영

```bash
# CTF 프로젝트 생성
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "ad-ctf-round1",
    "request_text": "Attack/Defense CTF 대규모 공방전 Round 1",
    "master_mode": "external"
  }'

# Flag 배치 (각 팀 서버)
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"echo \"FLAG{ad_ctf_$(openssl rand -hex 8)}\" > /opt/flag.txt && chmod 644 /opt/flag.txt","subagent_url":"http://10.20.30.80:8002"}'
```

## 실습 3.2: 방어 Phase (20분)

> **목적**: 서비스를 보호하면서 가용성을 유지한다
> **배우는 것**: 실시간 방어, 서비스 안정화

```bash
# 방어 태스크 실행
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"passwd -l nobody && cat /etc/passwd | grep -v nologin | grep -v false","risk_level":"medium","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"instruction_prompt":"chmod 600 /opt/flag.txt && chown root:root /opt/flag.txt","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"instruction_prompt":"nft add rule inet filter input tcp dport != { 22, 80, 443, 3000 } drop","risk_level":"medium","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'
```

## 실습 3.3: 공격 Phase (40분)

> **목적**: 상대 팀 서버에서 flag를 탈취한다
> **배우는 것**: 실전 침투, 제한 시간 내 공격

```bash
# 공격 태스크 실행
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"nmap -sV -T4 10.20.30.80 -p 1-10000","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"instruction_prompt":"nikto -h http://10.20.30.80:3000 -maxtime 60","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'

# SLA 체크 (서비스 가용성 확인)
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"curl -sI -o /dev/null -w \"%{http_code}\" http://10.20.30.80:3000","subagent_url":"http://localhost:8002"}'
```

## 실습 3.4: 스코어보드 업데이트

```bash
# 경기 결과 기록
curl -X POST http://localhost:8000/projects/{id}/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "A/D CTF Round 1 완료",
    "outcome": "success",
    "work_details": [
      "방어: 방화벽 설정, flag 권한 강화",
      "공격: 포트 스캔 + 웹 취약점 탐색 수행",
      "SLA: 서비스 가용성 100% 유지",
      "Flag: 1개 획득, 0개 유출"
    ]
  }'
```

---

# Part 4: 디브리핑 및 운영 노하우 (40분)

## 4.1 디브리핑 프로세스

| 항목 | 질문 |
|------|------|
| 공격 | 어떤 기법이 가장 효과적이었는가? |
| 방어 | 어떤 공격을 탐지하지 못했는가? |
| 팀워크 | 역할 분담은 적절했는가? |
| 도구 | 어떤 도구가 가장 유용했는가? |
| 개선 | 다음 라운드에서 무엇을 바꿀 것인가? |

## 4.2 CTF 운영 팁

- **인프라**: 팀별 독립 네트워크 세그먼트 필수
- **모니터링**: 전체 트래픽 미러링으로 공정성 확보
- **SLA 체크**: 자동화된 주기적 서비스 가용성 검증
- **Flag 로테이션**: 주기적 flag 변경으로 재사용 방지
- **에스컬레이션**: 인프라 장애 vs 공격 구분 절차

---

## 검증 체크리스트
- [ ] A/D CTF 규칙과 점수 체계를 설명할 수 있다
- [ ] 팀 역할 분담을 설계할 수 있다
- [ ] 방어 우선 전략(패치 → 방화벽 → 모니터링)을 실행할 수 있다
- [ ] 제한 시간 내에 공격과 방어를 동시에 수행할 수 있다
- [ ] 디브리핑을 통해 개선 포인트를 도출할 수 있다

## 자가 점검 퀴즈
1. A/D CTF에서 "방어 먼저" 전략이 중요한 이유를 점수 체계 관점에서 설명하시오.
2. SLA 점수와 공격 점수 사이의 트레이드오프는?
3. 4인 팀에서 1명이 공격에만 집중하는 것이 위험한 이유는?
4. Flag 로테이션이 없으면 어떤 문제가 발생하는가?
5. CTF 경기 중 자기 서버가 해킹당했을 때의 긴급 대응 절차를 5단계로 서술하시오.
