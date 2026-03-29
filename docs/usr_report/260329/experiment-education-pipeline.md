# 실험: OpsClaw 보안 교육 파이프라인 실증

## 실험 목적
OpsClaw가 **System → Education → Novel → CTF** 4계층 보안 교육 파이프라인의
중심 오케스트레이터로서 작동함을 실증한다.

## 가설
> "하나의 보안 주제가 OpsClaw를 매개로 4계층을 관통할 때,
> 각 계층의 산출물이 OpsClaw evidence에 통합 기록되어
> 학습의 완전성(completeness)과 추적 가능성(traceability)을 보장한다."

## 실험 설계

### 독립 변수
- 보안 주제 3개 (난이도 상이)
  - Topic A: nftables 방화벽 (C2W02, 초급)
  - Topic B: Wazuh 경보 분석 (C5W05, 중급)
  - Topic C: LLM 프롬프트 인젝션 방어 (C8W02, 고급)

### 종속 변수
각 주제별로 4계층의 산출물 측정:

| 계층 | 산출물 | 측정 |
|------|--------|------|
| System | OpsClaw dispatch/execute-plan 결과 | evidence 수, 성공률, 실행 시간 |
| Education | 교안 커버리지 | 해당 교안의 핵심 개념 포함 여부 |
| Novel | 소설 챕터 매핑 | 해당 기술이 소설에서 서사적으로 다뤄지는지 |
| CTF | 문제 풀이 | FLAG 획득 여부, 소요 시간 |

### 통합 지표
- **파이프라인 완전성**: 4계층 모두 evidence가 연결되는 비율
- **추적 가능성**: 하나의 project에서 4계층 산출물을 모두 replay 가능한지
- **교육 효과 시뮬레이션**: 계층별 난이도 대비 evidence 품질

## 실험 절차

### Topic A: nftables 방화벽 (C2W02)
```
1. [Education] 교안 참조 → 핵심 개념 추출
2. [System]    OpsClaw로 v-secu에 nftables 룰 적용
3. [Novel]     소설 1권 4장 "벽돌 쌓기"에서 해당 장면 확인
4. [CTF]       CTF 문제 "nftables로 IP 차단" 풀이
5. [통합]      하나의 OpsClaw 프로젝트에 4계층 evidence 통합
```

### Topic B: Wazuh 경보 분석 (C5W05)
### Topic C: LLM 프롬프트 인젝션 방어 (C8W02)
(동일 구조)

---

## 실험 결과

### 최종 통합 실행 결과

**프로젝트**: `exp-pipeline-FINAL`
**실행 방식**: execute-plan, 12개 태스크 병렬 실행 (3대 서버 동시)
**결과**: 12/12 성공, Evidence 12건 자동 생성, PoW 12블록

```
Overall: success | Tasks: 12, OK: 12, Failed: 0

Topic A — nftables 방화벽 (C2W02, 초급):
  ✅ Education: 교안 참조 → "nftables의 기본 구조(Table, Chain, Rule)"
  ✅ System:    v-secu에서 nftables drop 룰 1건 확인
  ✅ Novel:     vol01/ch04에서 nft 관련 3개 매칭
  ✅ CTF:       FLAG{drop} 획득

Topic B — Wazuh 경보 분석 (C5W05, 중급):
  ✅ Education: 교안 참조 → "보안 경보(Alert)의 분류 체계"
  ✅ System:    v-siem에서 Wazuh 경보 305건 확인
  ✅ Novel:     vol01/ch02에서 Wazuh 관련 2개 매칭
  ✅ CTF:       FLAG{5712} 획득

Topic C — 프롬프트 인젝션 방어 (C8W02, 고급):
  ✅ Education: 교안 참조 → "프롬프트 인젝션의 개념과 두 가지 유형"
  ✅ System:    OpsClaw dispatch 인젝션 방어 검증
  ✅ Novel:     vol02/ch08에서 injection 관련 2개 매칭
  ✅ CTF:       FLAG{prompt_injection_blocked} 획득
```

### 정량적 결과

| 지표 | 값 |
|------|-----|
| 전체 태스크 | 12 (3 Topics × 4 Layers) |
| 성공 | 12/12 (100%) |
| Evidence 자동 생성 | 12건 |
| PoW 블록 생성 | 12블록 (SHA-256, difficulty=4) |
| 성공률 | 1.0 (100%) |
| 사용 서버 | 3대 (opsclaw, v-secu, v-siem) |
| 실행 시간 | 병렬 실행, ~3초 |

### 파이프라인 완전성 검증

```
┌─────────────────────────────────────────────────────────┐
│  4계층 파이프라인 완전성 (Completeness)                    │
├─────────┬──────────┬──────────┬──────────┬──────────────┤
│ Topic   │ Edu      │ System   │ Novel    │ CTF          │
├─────────┼──────────┼──────────┼──────────┼──────────────┤
│ A(초급) │ ✅ ev_01 │ ✅ ev_02 │ ✅ ev_03 │ ✅ ev_04     │
│ B(중급) │ ✅ ev_05 │ ✅ ev_06 │ ✅ ev_07 │ ✅ ev_08     │
│ C(고급) │ ✅ ev_09 │ ✅ ev_10 │ ✅ ev_11 │ ✅ ev_12     │
├─────────┼──────────┴──────────┴──────────┴──────────────┤
│ 합계    │ 12/12 evidence (100% 완전성)                   │
└─────────┴───────────────────────────────────────────────┘
```

### 추적 가능성 검증 (Traceability)

하나의 OpsClaw 프로젝트(`exp-pipeline-FINAL`)에서:
- **replay** API로 12개 태스크의 실행 타임라인 재현 가능
- **evidence/summary**로 전체 성공률 확인 가능
- **PoW 체인**으로 각 태스크의 실행 시점 + 결과 해시 검증 가능
- 각 evidence에 `subagent_url`이 기록 → 어느 서버에서 실행됐는지 추적 가능

### 교육 효과 분석

| 계층 | 역할 | OpsClaw 기능 |
|------|------|-------------|
| **Education** | 이론 학습 | dispatch로 교안 내용 참조 → evidence 기록 |
| **System** | 실습 수행 | dispatch/execute-plan으로 실제 서버 조작 → evidence 자동 생성 |
| **Novel** | 서사적 맥락 | dispatch로 소설 챕터 매핑 확인 → 기술이 스토리에서 어떻게 쓰이는지 |
| **CTF** | 검증/평가 | FLAG 획득 → evidence가 "문제를 풀었다"의 증거 |

**OpsClaw의 역할**:
- 4계층의 **오케스트레이터**: 모든 작업이 OpsClaw를 통해 실행
- **증적 관리자**: 각 계층의 산출물이 evidence로 통합 기록
- **위변조 방지**: PoW 해시 체인으로 증적의 무결성 보장
- **학습 추적**: 하나의 프로젝트에서 학습의 전체 경로를 replay

## 결론

### 가설 검증 결과
> ✅ **검증됨**: 하나의 보안 주제가 OpsClaw를 매개로 4계층을 관통할 때,
> 각 계층의 산출물이 OpsClaw evidence에 통합 기록되어
> 학습의 완전성(100%)과 추적 가능성(replay+PoW)을 보장한다.

### 핵심 발견
1. **통합 오케스트레이션**: 3개 난이도 × 4계층 = 12개 태스크를 하나의 execute-plan으로 병렬 실행 가능
2. **자동 증적 생성**: 학생이 별도로 보고서를 작성하지 않아도, OpsClaw evidence가 "무엇을 했는지"의 증거
3. **교차 검증**: Education 교안의 핵심 개념 → System에서 실제 적용 → Novel에서 맥락 확인 → CTF로 평가
4. **PoW 기반 무결성**: 학생의 실습 기록이 위변조 불가능한 PoW 체인에 기록 → 공정한 평가 근거

### 실용적 시사점
- **교수자**: 학생의 실습 수행 여부를 evidence로 확인 가능 (수작업 검사 불필요)
- **학습자**: 자신의 학습 경로를 replay로 복기 가능
- **평가자**: PoW 체인 검증으로 부정행위 방지 (evidence 위조 불가)
- **콘텐츠 개발자**: YAML 문제 정의 + register_challenges.py로 CTF 문제 추가 자동화
