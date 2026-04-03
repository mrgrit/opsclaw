# Week 11: 레드팀 운영 — 작전 계획, 침투, 보고서 (PTES)

## 학습 목표
- PTES(Penetration Testing Execution Standard) 프레임워크를 이해하고 적용할 수 있다
- 레드팀 작전 계획서(Rules of Engagement)를 작성할 수 있다
- 체계적인 침투 테스트 절차를 수행할 수 있다
- 전문적인 침투 테스트 보고서를 작성할 수 있다
- OpsClaw를 레드팀 작전 관리 플랫폼으로 활용할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 01-05 공격 기법 전반 이해
- 기술 문서 작성 능력

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 레드팀 기지 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽 (투과 대상) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 공격 대상 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | 탐지 현황 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | PTES 프레임워크 및 ROE | 강의 |
| 0:35-1:10 | 작전 계획서 작성 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:20 | 침투 테스트 실전 실습 | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | 보고서 작성 실습 | 실습 |
| 3:10-3:30 | 보고서 리뷰 + 퀴즈 | 토론 |

---

# Part 1: PTES 프레임워크 (35분)

## 1.1 PTES 7단계

| 단계 | 이름 | 핵심 산출물 |
|------|------|------------|
| 1 | Pre-engagement Interactions | ROE, 범위 정의 |
| 2 | Intelligence Gathering | 정찰 결과 문서 |
| 3 | Threat Modeling | 위협 모델, 공격 트리 |
| 4 | Vulnerability Analysis | 취약점 목록 |
| 5 | Exploitation | 침투 증거 |
| 6 | Post-Exploitation | 영향도 평가 |
| 7 | Reporting | 최종 보고서 |

## 1.2 Rules of Engagement (ROE)

ROE는 침투 테스트의 **법적/기술적 경계**를 정의하는 핵심 문서이다.

```markdown
## ROE 필수 항목
1. 테스트 범위 (In-Scope / Out-of-Scope)
2. 허용 기법 (소셜 엔지니어링, 물리적 침투 등)
3. 테스트 시간대 (업무 시간 / 비업무 시간)
4. 금지 행위 (DoS, 데이터 파괴 등)
5. 긴급 연락처 (에스컬레이션 절차)
6. 데이터 처리 (수집 데이터 보관/파기)
7. 법적 면책 조항
```

## 1.3 레드팀 vs 침투 테스트

| 특성 | 침투 테스트 | 레드팀 |
|------|-----------|--------|
| 목표 | 취약점 발견 | 보안 체계 평가 |
| 기간 | 1-2주 | 수 주~수 개월 |
| 범위 | 정해진 대상 | 전체 조직 |
| 은밀성 | 알림 방어팀 | 비밀 수행 |
| 보고 | 취약점 목록 | 공격 시나리오 + 방어 개선안 |

---

# Part 2: 작전 계획서 작성 실습 (35분)

## 실습 2.1: ROE 문서 작성

> **목적**: 실전 레드팀 작전을 위한 ROE를 작성한다
> **배우는 것**: 법적/기술적 경계 설정

```markdown
# Red Team Operation - ROE
## 작전명: Operation Shadow Strike
## 날짜: 2026-04-03
## 대상 조직: Lab Environment (10.20.30.0/24)

### 범위
- In-Scope: 10.20.30.80 (웹 서버), 10.20.30.100 (SIEM)
- Out-of-Scope: 10.20.30.1 (방화벽 - 직접 공격 금지)

### 허용 기법
- [O] 네트워크 스캐닝, 웹 취약점 공격
- [O] 자격증명 크래킹 (오프라인)
- [X] DoS/DDoS 공격
- [X] 물리적 접근
- [X] 소셜 엔지니어링

### 긴급 연락처
- 기술 담당: admin@lab.local
- 에스컬레이션: 서비스 장애 발생 시 즉시 중단
```

## 실습 2.2: OpsClaw 작전 프로젝트 생성

```bash
# 레드팀 작전 프로젝트 생성
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "redteam-shadow-strike",
    "request_text": "레드팀 작전: 웹 서버 침투 + Post-Exploitation + 보고서",
    "master_mode": "external"
  }'
```

---

# Part 3: 침투 테스트 실전 실습 (60분)

## 실습 3.1: 체계적 침투 절차

> **목적**: PTES에 따라 정찰부터 Post-Exploitation까지 수행한다
> **배우는 것**: 체계적 침투 절차, 증거 수집

```bash
# Stage 1: 정찰
curl -X POST http://localhost:8000/projects/{id}/plan -H "X-API-Key: $OPSCLAW_API_KEY"
curl -X POST http://localhost:8000/projects/{id}/execute -H "X-API-Key: $OPSCLAW_API_KEY"

# PTES Phase 2: Intelligence Gathering
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"nmap -sV -sC -O 10.20.30.80 -oN /tmp/recon.txt","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"instruction_prompt":"curl -sI http://10.20.30.80:3000 && nikto -h http://10.20.30.80:3000 -o /tmp/nikto.txt","risk_level":"low","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'

# PTES Phase 4-5: Vulnerability Analysis + Exploitation
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"curl -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"admin@juice-sh.op\\\",\\\"password\\\":\\\"admin123\\\"}\"","risk_level":"medium","subagent_url":"http://localhost:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'

# 증거 수집
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/{id}/evidence/summary
```

---

# Part 4: 보고서 작성 (40분)

## 4.1 침투 테스트 보고서 구조

```markdown
# 침투 테스트 보고서

## 1. 요약 (Executive Summary)
- 대상, 기간, 범위, 주요 발견 사항

## 2. 발견 사항 (Findings)
### Finding #1: SQL Injection
- 심각도: Critical (CVSS 9.8)
- 위치: /rest/user/login
- 설명: 인증 우회 가능
- 재현 절차: [단계별 설명]
- 증거: [스크린샷/로그]
- 권장 조치: 파라미터 검증, PreparedStatement 사용

## 3. ATT&CK 매핑
| 기법 | ID | 결과 |
|------|-----|------|
| Exploit Public-Facing App | T1190 | 성공 |

## 4. 위험도 분류
- Critical: 1건, High: 2건, Medium: 3건

## 5. 권장 사항
- 단기 (1주): 패치 적용
- 중기 (1개월): WAF 규칙 추가
- 장기 (3개월): 보안 개발 교육
```

## 4.2 OpsClaw 완료 보고서 생성

```bash
curl -X POST http://localhost:8000/projects/{id}/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "레드팀 작전 Shadow Strike 완료",
    "outcome": "success",
    "work_details": [
      "정찰: nmap + nikto 스캔 완료",
      "취약점: SQL Injection (Critical) 1건 발견",
      "침투: 인증 우회 성공, 관리자 권한 획득",
      "권장: PreparedStatement 적용, WAF 규칙 추가"
    ]
  }'
```

---

## 검증 체크리스트
- [ ] PTES 7단계를 순서대로 설명할 수 있다
- [ ] ROE 문서의 필수 항목을 빠짐없이 작성할 수 있다
- [ ] 체계적 침투 절차에 따라 테스트를 수행할 수 있다
- [ ] 전문적인 침투 테스트 보고서를 작성할 수 있다
- [ ] OpsClaw로 레드팀 작전 전 과정을 관리할 수 있다

## 자가 점검 퀴즈
1. ROE에서 "Out-of-Scope" 대상을 실수로 공격했을 때의 법적 리스크와 대응 절차는?
2. PTES의 Pre-engagement 단계가 중요한 이유를 3가지 서술하시오.
3. 침투 테스트 보고서에서 Executive Summary를 비기술 경영진이 이해할 수 있게 작성하는 요령은?
4. 레드팀 작전에서 "탐지됨"과 "탐지 안됨"이 모두 유용한 결과인 이유는?
5. CVSS 점수 산정 시 고려하는 주요 메트릭 3가지를 설명하시오.
