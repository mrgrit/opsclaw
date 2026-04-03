# OpsClaw 시스템 분할 로드맵 (3+1 아키텍처)

**작성일:** 2026-04-03  
**현재 상태:** OpsClaw 모놀리스 (M28 완료), bastion 분석 프로젝트 존재  
**목적:** 모놀리스 OpsClaw를 3개 배포 가능 시스템 + 중앙서버로 분할

---

## 1. 타겟 아키텍처 개요

```
                    ┌─────────────────────────────┐
                    │       중앙서버 (:7000)        │
                    │  인스턴스 관리 / 통합 블록체인  │
                    │  CTF 서버 / 배포 패키지 / NMS  │
                    └──────┬──────┬──────┬─────────┘
                           │      │      │
              ┌────────────┘      │      └────────────┐
              ▼                   ▼                    ▼
    ┌──────────────┐    ┌──────────────┐     ┌──────────────┐
    │ bastion :9000 │    │  CCC :9100   │     │opsclaw :8000 │
    │  실무 운영/보안 │    │  교육 플랫폼  │     │  연구/개발    │
    │  AI 에이전트   │    │ Non-AI / AI  │     │  풀 기능      │
    └──────┬───────┘    └──────┬───────┘     └──────────────┘
           │                   │
     ┌─────┴─────┐      ┌─────┴─────┐
     │ SubAgent  │      │  학생 인프라  │
     │ :8002 각  │      │  개별 VM     │
     └───────────┘      └───────────┘
```

| 시스템 | 용도 | 레포 | 포트 |
|--------|------|------|------|
| **opsclaw** | 연구/개발 (현행 유지) | github.com/mrgrit/opsclaw | :8000 |
| **중앙서버** | 통합 관리 | opsclaw 레포 내 `apps/central-server/` | :7000 |
| **CCC** | 사이버보안 교육 | github.com/mrgrit/ccc | :9100 |
| **bastion** | 실무 운영/보안 에이전트 | github.com/mrgrit/bastion | :9000 |

---

## 2. 마일스톤 개요

| MS | 이름 | 대상 레포 | 의존성 | 핵심 산출물 |
|----|------|----------|--------|------------|
| **M1** | 공유 기반 패키지 추출 | opsclaw | 없음 | opsclaw-common 독립 패키지, 공유 프로토콜 |
| **M2** | 중앙서버 API 설계 | opsclaw | M1 | 중앙서버 API 스펙, 인스턴스/블록체인 동기화 프로토콜 |
| **M3** | bastion 코어 | bastion | M1 | bastion-api, 자산 온보딩, SubAgent 자동 설치 |
| **M4** | bastion 대시보드 | bastion | M3 | bastion-ui, 자산/에이전트 현황 대시보드 |
| **M5** | bastion AI 에이전트 | bastion | M3, M4 | AI 운영/보안 자동화, CLI/웹 인터페이스 |
| **M6** | 중앙서버 코어 구현 | opsclaw | M2, M3 | 인스턴스 관리, 통합 블록체인, CTF 서버, 배포 패키지 |
| **M7** | CCC 공통 기반 | ccc | M1, M6 | 인프라 자동 구축, CTF 클라이언트, 실습 엔진, 학생 관리 |
| **M8** | CCC Non-AI 커리큘럼 | ccc | M7 | 수동 공격/방어/분석 실습, 대전 모드 기본 |
| **M9** | CCC AI 커리큘럼 | ccc | M7, M5 | bastion 연동 AI 실습, AI 대전 |
| **M10** | 대전 모드 + 리더보드 | ccc | M8, M9 | 실시간 시각화, 관전 모드, 종합 리더보드 |
| **M11** | 중앙서버 고도화 | opsclaw | M6 | NMS/SMS, 통합 관리자 대시보드 |
| **M12** | 통합 테스트 + 배포 자동화 | 전체 | M5, M10, M11 | E2E 테스트, Docker/systemd 배포, 문서화 |

### 타임라인

```
Week  1-2:  [M1 공유 패키지 추출]
Week  3-4:  [M2 중앙서버 설계] + [M3 bastion 코어]  ← 병렬
Week  5-6:  [M4 bastion UI] + [M3 완료]
Week  6-8:  [M5 bastion AI]
Week  7-9:  [M6 중앙서버 코어]
Week  9-12: [M7 CCC 공통]
Week 12-14: [M8 Non-AI] + [M9 AI]  ← 부분 병렬
Week 14-16: [M10 대전 모드]
Week 16-17: [M11 중앙서버 고도화]
Week 18-20: [M12 통합 테스트]
```

---

## 3. 패키지 재사용 전략

```
opsclaw-common (git submodule + pip install -e)
├── a2a_protocol       → bastion, ccc 모두 사용
├── pow_service        → 블록체인 (모두 사용)
├── evidence_service   → 작업 증거 (모두 사용)
├── bootstrap_service  → SubAgent 원격 설치 (모두 사용)
├── asset_registry     → 자산 관리 (bastion 위주, ccc도 인프라 관리)
├── project_service    → DB 연결 추상화 (모두 사용)
└── protocol/          → 중앙서버 통신 프로토콜 (신규)

bastion 전용
├── agent_orchestrator → pi_adapter + prompt_engine 활용
└── infra_scanner      → 자산 자동 탐색

ccc 전용
├── student_manager    → 학생 관리/진도/평가
├── lab_engine         → 실습 엔진 (YAML 시나리오, 검증, 블록체인)
├── ctf_client         → 중앙 CTF 서버 클라이언트
├── battle_engine      → 대전 엔진 (공방전)
└── infra_bootstrap    → 학생 PC VM 자동 구축

중앙서버 전용 (opsclaw 레포 내)
├── instance_manager   → 인스턴스 관리
├── unified_blockchain → 통합 블록체인
├── ctf_server         → CTF 서버
└── package_manager    → 배포 패키지
```

---

## 4. 마일스톤 상세

---

### M1: 공유 기반 패키지 추출 (opsclaw-common)

**목표:** 3개 시스템이 공통으로 사용할 패키지를 독립 Python 패키지로 추출

#### 구조

```
opsclaw-common/
├── pyproject.toml
├── src/opsclaw_common/
│   ├── a2a/              # a2a_protocol
│   ├── blockchain/       # pow_service
│   ├── evidence/         # evidence_service
│   ├── bootstrap/        # bootstrap_service
│   ├── asset/            # asset_registry
│   ├── project/          # project_service (DB 연결 추상화)
│   ├── models/           # 공유 Pydantic 모델
│   └── protocol/         # 중앙서버 통신 프로토콜
```

#### TODO

- [ ] opsclaw 패키지 의존성 그래프 작성
- [ ] `project_service.get_connection()` DB 연결을 설정 주입 방식으로 리팩토링
- [ ] `pow_service` DB 직접 의존 제거, Repository 패턴 도입
- [ ] `asset_registry._conn()` 하드코딩 제거
- [ ] `a2a_protocol.A2AClient`에 인증 헤더 추가
- [ ] Central Protocol 메시지 스키마 정의 (Pydantic)
- [ ] 공통 DB 마이그레이션 분리
- [ ] opsclaw-common 빌드/설치 테스트
- [ ] opsclaw 모놀리스가 opsclaw-common을 의존성으로 사용하도록 전환

#### 설계 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| 배포 방식 | Git submodule + pip editable | 사설 PyPI 없이 빠르게 시작 |
| DB 추상화 | Repository 패턴 + DI | 시스템별 DB URL 독립 설정 |
| 프로토콜 전송 | HTTPS + API Key + 인스턴스 서명 | 내부망 기본 인증, 향후 mTLS 확장 |
| 블록체인 동기화 | Push 기반 (엣지→중앙) | 엣지가 블록 생성 후 중앙에 푸시 |

---

### M2: 중앙서버 프로토콜 및 API 설계

**목표:** 중앙서버 API 스펙과 데이터 모델 확정

#### API 영역

| 영역 | 경로 | 기능 |
|------|------|------|
| 인스턴스 관리 | `/instances/` | 등록, 상태, 하트비트, 목록 |
| 통합 블록체인 | `/blockchain/` | 블록 수신, 통합 체인, 검증, 리더보드 |
| CTF 서버 | `/ctf/` | 문제 CRUD, 플래그 검증, 스코어보드 |
| 배포 패키지 | `/packages/` | 업로드, 버전, 다운로드 |
| 실험 인프라 | `/experiments/` | 테스트 인스턴스 CRUD |
| 관리자 | `/admin/` | 대시보드 데이터 |

#### TODO

- [ ] OpenAPI 3.0 스펙 작성 (`schemas/central-api.yaml`)
- [ ] 인스턴스 등록/인증 플로우 시퀀스 다이어그램
- [ ] 블록체인 동기화 프로토콜 상세 설계 (충돌 해결 포함)
- [ ] CTF 서버 API 설계
- [ ] 배포 패키지 관리 API 설계
- [ ] DB 마이그레이션 설계 (중앙서버 전용 테이블)

#### 블록체인 통합 전략

```
각 인스턴스: 로컬 pow_service로 자체 체인 유지
     ↓ 블록 생성 시 비동기 푸시
중앙서버: 인스턴스별 체인 수집 → 통합 검증 뷰
     - 교차 인스턴스 agent_id 충돌 감지
     - 통합 리더보드 (전체 시스템)
```

---

### M3: bastion 코어 — 자산 등록 + SubAgent 자동 설치

**목표:** bastion을 독립 실행 가능한 시스템으로 구축

#### 구조

```
bastion/                          # ~/bastion/
├── CLAUDE.md
├── pyproject.toml
├── apps/
│   ├── bastion-api/              # FastAPI :9000
│   │   └── src/main.py
│   └── bastion-ui/               # React (web-ui 경량 포크)
├── packages/
│   ├── agent_orchestrator/       # AI 오케스트레이션 (M5)
│   └── infra_scanner/            # 자산 자동 탐색
├── migrations/
├── deploy/
├── docker/
├── docs/                         # 기존 분석 문서 유지
└── scripts/
```

#### bastion-api 엔드포인트

| 메서드 | 경로 | 기능 |
|--------|------|------|
| POST | `/assets` | 자산 등록 |
| POST | `/assets/{id}/bootstrap` | SubAgent 원격 설치 |
| GET | `/assets/{id}/health` | 헬스체크 |
| GET | `/assets` | 자산 목록 |
| POST | `/assets/{id}/onboard` | 전체 온보딩 (등록+부트스트랩+resolve) |
| POST | `/central/register` | 중앙서버 등록 |

#### 자산 온보딩 플로우

```
관리자 → 자산 정보 입력 (IP, OS, 역할)
  → bastion-api → asset_registry.onboard_asset()
  → SSH 접속 → SubAgent 자동 설치
  → 헬스체크 → SubAgent /health 응답 확인
  → 자산 상태 = "healthy"
  → (M6 이후) 중앙서버에 동기화
```

#### TODO

- [ ] bastion 프로젝트 구조 초기화
- [ ] opsclaw-common git submodule 추가
- [ ] bastion-api FastAPI 앱 생성 (자산 CRUD)
- [ ] asset_registry, bootstrap_service 연동 테스트
- [ ] bastion 전용 DB 마이그레이션
- [ ] Docker Compose (bastion-api + PostgreSQL)
- [ ] A2A 프로토콜 SubAgent 통신 테스트
- [ ] bastion CLI 스캐폴딩

---

### M4: bastion 대시보드 + 관리 UI

**목표:** 자산 현황, SubAgent 상태, 작업 이력 대시보드

#### 신규 페이지

| 페이지 | 기능 |
|--------|------|
| Dashboard | 자산 총계, 건강 상태, 최근 작업 타임라인 |
| Assets | 자산 목록/상세/등록/삭제, SubAgent 상태 |
| Operations | 작업 이력, 실행 중 작업 |
| Blockchain | 블록 목록, 체인 검증 |
| Settings | bastion 설정, 중앙서버 연동 |

#### TODO

- [ ] opsclaw web-ui에서 bastion-ui 포크 (Layout, 스타일, API 유틸)
- [ ] Dashboard 페이지 (통계 차트)
- [ ] Assets 페이지 (CRUD + 실시간 상태)
- [ ] Operations 페이지 (작업 이력)
- [ ] Blockchain 페이지 (블록 + 검증)
- [ ] Settings 페이지
- [ ] bastion-api 대시보드 엔드포인트 추가
- [ ] 빌드 + 정적 파일 서빙 설정

---

### M5: bastion AI 에이전트 — 운영/보안 자동화

**목표:** CLI/웹으로 자연어 작업 요청 → AI 계획 수립 → SubAgent 실행 → 블록체인 기록

#### AI 작업 플로우

```
사용자: "secu 서버에 Suricata 룰 업데이트해줘"
  → bastion-api → agent_orchestrator.plan(task)
  → prompt_engine.compose("bastion") + 자산 컨텍스트
  → pi_adapter → LLM (Ollama) → 실행 계획 생성
  → hook_engine.fire("pre_dispatch") → permission_engine.check()
  → a2a_protocol → SubAgent(secu:8002) → 명령 실행
  → pow_service.generate_proof() → 블록 생성
  → cost_tracker 기록 → 결과 반환
```

#### bastion-api AI 엔드포인트

| 메서드 | 경로 | 기능 |
|--------|------|------|
| POST | `/agent/task` | AI 작업 요청 (자연어→실행) |
| GET | `/agent/task/{id}` | 작업 상태/결과 |
| POST | `/agent/analyze` | 시스템 분석 요청 |
| GET | `/agent/recommendations` | RL 기반 추천 |

#### bastion CLI

```bash
bastion task "시스템 패치 적용"    # AI 작업 요청
bastion status                    # 작업 상태
bastion analyze "디스크 분석"     # 분석 요청
```

#### TODO

- [ ] `agent_orchestrator` 패키지 생성
- [ ] bastion 전용 시스템 프롬프트 섹션
- [ ] Task → PoW 연동 플로우
- [ ] bastion-api AI 엔드포인트
- [ ] bastion-ui Agent 페이지 (작업 요청 폼, 결과 뷰)
- [ ] bastion CLI AI 명령
- [ ] rl_service, cost_tracker, permission_engine 연동
- [ ] E2E: 자산 등록 → AI 작업 → SubAgent 실행 → 블록 생성

---

### M6: 중앙서버 코어 구현

**목표:** 인스턴스 관리, 통합 블록체인, CTF 서버, 배포 패키지 관리

#### 구조 (opsclaw 레포 내 추가)

```
opsclaw/apps/
├── central-server/       # 신규 :7000
│   └── src/
│       ├── main.py
│       ├── instance_routes.py
│       ├── blockchain_routes.py
│       ├── ctf_routes.py
│       └── package_routes.py
└── central-ui/           # 신규: 중앙 관리 대시보드 (React)

opsclaw/packages/
├── instance_manager/     # 신규
├── unified_blockchain/   # 신규
├── ctf_server/           # 신규
└── package_manager/      # 신규
```

#### 블록체인 통합

```
bastion A: [B1]→[B2]→[B3]  (agent: secu:8002)
bastion B: [B1]→[B2]        (agent: web:8002)
CCC C:     [B1]→[B2]→[B3]→[B4]  (agent: student1)
        │
        ▼ POST /central/blocks/sync
중앙서버:
  - 인스턴스별 체인 독립 검증
  - 통합 타임라인 (전체 블록 시간순)
  - 통합 리더보드 (모든 인스턴스 reward 합산)
  - agent_id 충돌 감지
```

#### TODO

- [ ] central-server FastAPI 앱 (:7000)
- [ ] `instance_manager` (등록, 하트비트, 상태)
- [ ] `unified_blockchain` (블록 수신, 통합 체인, 검증)
- [ ] `ctf_server` (문제 관리, 플래그 검증, 스코어보드)
- [ ] `package_manager` (패키지 저장, 버전, 다운로드)
- [ ] 중앙서버 DB 마이그레이션 (`0016_central_server.sql`)
- [ ] bastion 연동 테스트 (등록→하트비트→블록 동기화)
- [ ] 기존 `contents/ctf/challenges/` CTF 엔진 로드
- [ ] central-ui 스캐폴딩

---

### M7: CCC 공통 기반 — 부트스트랩 + CTF + 실습 엔진

**목표:** CCC 프로젝트 구축, 학생 인프라 자동 구축, 실습 엔진

#### 구조

```
ccc/                              # ~/ccc/
├── CLAUDE.md
├── pyproject.toml
├── apps/
│   ├── ccc-api/                  # FastAPI :9100
│   │   └── src/
│   │       ├── main.py
│   │       ├── student_routes.py
│   │       ├── lab_routes.py
│   │       ├── ctf_routes.py
│   │       └── battle_routes.py
│   ├── ccc-ui/                   # React 웹 UI
│   │   └── src/pages/
│   │       ├── Dashboard.tsx     # 진도, 랭킹, 최근 활동
│   │       ├── Labs.tsx          # 실습 목록, 시작/완료
│   │       ├── CTF.tsx           # 문제, 제출, 스코어보드
│   │       ├── Battle.tsx        # 대전 생성/참가/관전
│   │       ├── Leaderboard.tsx   # 종합 랭킹
│   │       ├── Terminal.tsx      # SSH 접속
│   │       └── Progress.tsx      # 과목별 진도
│   └── ccc-cli/                  # 학생용 CLI
├── packages/
│   ├── student_manager/          # 학생 관리
│   ├── lab_engine/               # 실습 엔진 (YAML 시나리오)
│   ├── ctf_client/               # 중앙 CTF 클라이언트
│   ├── battle_engine/            # 대전 엔진
│   └── infra_bootstrap/          # 학생 인프라 구축
├── contents/
│   ├── labs/                     # 실습 시나리오
│   └── curriculum/               # 커리큘럼 정의
├── migrations/
├── docker/
└── scripts/
    └── student-setup.sh          # 학생 PC 초기 설정
```

#### 핵심 기능

1. **학생 인프라 자동 구축**: `student-setup.sh` → VM 환경 자동 생성 → CCC 중앙에 등록
2. **실습 엔진**: YAML 시나리오 → 환경 검증 → 실습 → 결과 검증 → PoW 블록 생성
3. **CTF 클라이언트**: 중앙서버 CTF API 연동, 문제 조회/제출/채점
4. **학생 관리**: 등록, 진도 추적, AI 학습 분석/피드백

#### TODO

- [ ] CCC 프로젝트 구조 초기화
- [ ] opsclaw-common submodule 추가
- [ ] `student_manager` (CRUD, 진도)
- [ ] `infra_bootstrap` (학생 PC VM 자동 구축)
- [ ] `student-setup.sh` (VirtualBox/KVM VM 생성)
- [ ] `lab_engine` (YAML 파서, 검증, 블록체인 기록)
- [ ] `ctf_client` (중앙서버 CTF API 클라이언트)
- [ ] ccc-api (학생/실습/CTF/인프라 라우트)
- [ ] ccc-ui 스캐폴딩 (opsclaw web-ui 포크 + 교육 최적화)
- [ ] opsclaw 교육 콘텐츠 → CCC labs YAML 변환
- [ ] CCC DB 마이그레이션
- [ ] 중앙서버 연동 테스트
- [ ] E2E: 인프라 등록 → 실습 → 블록체인 → 진도

---

### M8: CCC Non-AI — 수동 실습 커리큘럼

**목표:** AI 없이 수동으로 공격/방어/분석/대응 실습, 대전 모드 기본

#### 산출물

1. **수동 실습 시나리오**: 8과목 x 15주 = 120개 YAML (step-by-step 명령어, 검증)
2. **대전 모드 기본**: 공격자 vs 방어자, 수동 공방전, 블록체인 기록
3. **실습 평가 자동화**: lab_engine 자동 검증 → PoW 블록 → 중앙서버 동기화
4. **교수용 관리**: 전체 학생 진도, 대전 결과

#### TODO

- [ ] 8과목 x 15주 실습 시나리오 YAML 변환 (120개)
- [ ] 수동 실습 가이드 작성
- [ ] lab_engine 검증 로직 (시나리오별 성공 조건)
- [ ] `battle_engine` 기본 구현 (요청/수락/규칙/판정/블록체인)
- [ ] 리더보드 (개인/과목/대전)
- [ ] CCC-UI Labs/Battle/Progress 페이지 완성
- [ ] 교수용 관리 페이지
- [ ] E2E: 시나리오 → 검증 → 블록 → 진도

---

### M9: CCC AI — bastion 연동 AI 실습

**목표:** bastion AI 에이전트 활용, 웹/CLI 인터페이스 (raw curl 금지)

#### 산출물

1. **AI 실습 커리큘럼**: 기존 수동 실습의 AI 버전, Course 9-10 AI 특화
2. **bastion 연동 UI**: 구조화된 작업 요청 폼, 실행 과정 시각화, 결과 뷰
3. **AI 학습 분석**: 학생 이력 → LLM 분석 → 피드백, 맞춤 추천
4. **AI 대전**: AI vs AI, AI vs 수동, 에이전트 성능 평가

#### TODO

- [ ] AI 실습 시나리오 설계
- [ ] CCC → bastion 연동 인터페이스
- [ ] CCC-UI AI 실습 페이지 (작업 폼, 과정 시각화)
- [ ] CCC-CLI AI 명령 (`ccc ai-task`, `ccc ai-analyze`)
- [ ] AI 학습 분석 서비스
- [ ] AI 대전: AI vs AI, AI vs 수동
- [ ] Course 9, 10 AI 시나리오 YAML
- [ ] bastion 통합 테스트

---

### M10: 대전 모드 + 리더보드

**목표:** 인프라 간 공방전 완성, 실시간 시각화, 관전 모드

#### 대전 아키텍처

```
[학생A 인프라]           [CCC 중앙]           [학생B 인프라]
  공격자 ─────────→ battle_engine ←────────── 방어자
                        │
                   WebSocket
                        │
                 [관전자/리더보드]

1. 대전 요청 → 매칭
2. 대전 시작 → 타이머
3. 공격 ↔ 방어 (수동 or AI)
4. 이벤트 실시간 전송 → 시각화
5. 종료 → 판정 → 블록체인 → 리더보드
```

#### 대전 유형

| 유형 | 설명 |
|------|------|
| 1v1 | 공격자 vs 방어자 |
| 팀전 | 팀 vs 팀 |
| FFA | 다자간 자유 대전 |
| 수동vs수동 | 양측 수동 |
| AIvsAI | 양측 AI (학생이 에이전트 튜닝) |
| 수동vsAI | 혼합 |

#### TODO

- [ ] `battle_engine` 완성 (유형, 모드, 규칙, 매칭)
- [ ] WebSocket 실시간 이벤트 스트리밍
- [ ] 네트워크 토폴로지 시각화 (D3.js/vis.js)
- [ ] 타임라인 시각화
- [ ] 관전 모드 (WebSocket 구독)
- [ ] 종합 리더보드 (다차원 점수)
- [ ] 중앙서버 통합 리더보드 연동
- [ ] CCC-UI Battle/Leaderboard/Spectator 완성
- [ ] 대전 결과 블록체인 + 중앙서버 동기화

---

### M11: 중앙서버 고도화 — NMS/SMS + 대시보드

**목표:** 네트워크/시스템 모니터링, 통합 관리자 대시보드

#### 산출물

| 기능 | 설명 |
|------|------|
| NMS | 인스턴스 네트워크 상태, 연결/지연/가용성, 알림 |
| SMS | 시스템 리소스 (CPU/Mem/Disk), SubAgent 상태 집계 |
| 실험 인프라 | 테스트 인스턴스 생성/삭제, A/B 테스트 |
| 통합 대시보드 | 인스턴스 지도, 드릴다운, CTF 관리, NMS/SMS |

#### TODO

- [ ] NMS (ICMP ping, TCP probe, 연결 상태)
- [ ] SMS (리소스 메트릭, SubAgent 상태)
- [ ] 실험 인프라 API
- [ ] central-ui 완성 (지도, 드릴다운, CTF, NMS/SMS)
- [ ] 알림 연동 (notification_service)
- [ ] 실시간 갱신 (WebSocket)

---

### M12: 통합 테스트 + 배포 자동화

**목표:** E2E 테스트, 배포 자동화, 문서화

#### E2E 테스트 시나리오

| # | 시나리오 |
|---|---------|
| 1 | bastion 등록 → 중앙서버 → AI 작업 → 블록체인 동기화 |
| 2 | CCC 등록 → 학생 등록 → 실습 → 블록체인 → 중앙서버 동기화 |
| 3 | CCC 대전 → 실시간 시각화 → 블록체인 → 리더보드 |
| 4 | 중앙 CTF → CCC 문제 수신 → 풀기 → 제출 → 스코어보드 |
| 5 | 중앙서버 배포 패키지 → bastion/CCC 업데이트 |

#### TODO

- [ ] E2E 테스트 스크립트 (5개 시나리오)
- [ ] Docker Compose (bastion, ccc, central-server)
- [ ] systemd 유닛 파일
- [ ] 배포 스크립트 (`deploy-bastion.sh`, `deploy-ccc.sh`, `deploy-central.sh`)
- [ ] GitHub Actions CI/CD
- [ ] 시스템 아키텍처 다이어그램
- [ ] 설치/운영/사용자 가이드

---

## 5. DB 전략

```
opsclaw DB:   현행 유지 (전체 테이블)
bastion DB:   공통 테이블 (opsclaw-common) + bastion 전용 (bastion_config, operation_logs)
ccc DB:       공통 테이블 + ccc 전용 (students, courses, lab_completions, battles, rankings)
central DB:   공통 테이블 + 중앙서버 전용 (instances, unified_blocks, ctf_*, deploy_packages)
```

---

## 6. 웹 UI 전략

| 시스템 | 기반 | 변경 |
|--------|------|------|
| opsclaw | 기존 web-ui | 변경 없음 |
| bastion | web-ui 경량 포크 | Portal 제거, Dashboard+Assets+Agent만 |
| CCC | web-ui 포크 + 대폭 수정 | Labs/Battle/Leaderboard/Progress, Terminal/ChatBot 유지 |
| 중앙서버 | 신규 React 앱 | 인스턴스/블록체인/CTF/NMS/SMS |

---

## 7. 위험 요소

| 위험 | 영향 | 대응 |
|------|------|------|
| opsclaw-common 추출 시 opsclaw 파손 | 높음 | 점진적 마이그레이션, 호환성 테스트 필수 |
| 블록체인 동기화 충돌 | 중간 | 인스턴스별 독립 체인, 중앙은 집계만 |
| 학생 인프라 다양성 (OS/HW) | 높음 | Docker/VM 표준화, 최소 사양 정의 |
| 대전 모드 보안 | 높음 | 대전 범위 제한, 네트워크 격리, 방화벽 자동 |
| 공통 패키지 버전 충돌 | 중간 | SemVer, 릴리스 브랜치 |

---

## 8. 용어 정리

| 용어 | 설명 |
|------|------|
| **opsclaw** | 원본 연구용 모놀리스 (:8000) |
| **중앙서버** | 모든 인스턴스 관리 서버 (:7000) |
| **CCC** | Cyber Combat Commander, 교육용 (:9100) |
| **bastion** | 실무 운영/보안 에이전트 (:9000) |
| **opsclaw-common** | 공유 기반 Python 패키지 |
| **Central Protocol** | 중앙서버 ↔ 엣지 통신 프로토콜 |
| **lab_engine** | CCC 실습 엔진 |
| **battle_engine** | CCC 대전 엔진 |
| **SubAgent** | 원격 명령 실행 에이전트 (:8002) |
