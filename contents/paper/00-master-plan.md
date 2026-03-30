# OpsClaw 논문 시리즈 마스터 플랜

**작성일:** 2026-03-25
**총 논문 수:** 3편
**작성 언어:** 한국어 (Markdown)

---

## 전체 구조

```
Paper 1 (아키텍처 + 기반 검증)     ✅ 작성 완료
  ↓ 인용
Paper 2 (보안/모의해킹 실증)       ✅ 작성 완료
Paper 3 (실운영 사례 연구)         ⬜ 추가 실험 후 작성
```

---

## Paper 1 — 아키텍처 + 기반 검증 ✅

| 항목 | 내용 |
|------|------|
| **제목(안)** | OpsClaw: PoW 블록체인 기반 자기 개선형 에이전트 하네스 아키텍처 |
| **영문 제목(안)** | OpsClaw: A Self-Improving Agent Harness Architecture with Proof-of-Work Blockchain Verification |
| **핵심 주장** | 에이전트 실행의 무결성·재현성·자율 개선을 동시에 보장하는 하네스 아키텍처 |
| **실험** | 기반 검증 A~H (8개 실험) |
| **대상 학회** | 시스템/소프트웨어 아키텍처 (ICSA, ICSOC, SoCC) |
| **상태** | ✅ 전체 작성 완료 (8개 섹션 + 참고문헌 30편) |

## Paper 2 — 보안/모의해킹 자동화 실증 ✅

| 항목 | 내용 |
|------|------|
| **제목(안)** | LLM 에이전트 기반 자율 모의해킹 및 방어 자동화: MITRE ATT&CK 4-Tier 실증 연구 |
| **영문 제목(안)** | Autonomous Penetration Testing and Defense Automation with LLM Agents: A MITRE ATT&CK 4-Tier Empirical Study |
| **핵심 주장** | LLM 에이전트가 Red/Blue/Purple Team 보안 운용을 자율적으로 수행 가능 |
| **실험** | Red T1~T4 (21/27, 77.8%), Blue T1 (12/16), Purple 4회전 |
| **대상 학회** | 보안 (USENIX Security, ACSAC, RAID) |
| **상태** | ✅ 전체 작성 완료 (8개 섹션) |

## Paper 3 — 실운영 사례 연구 ⬜

| 항목 | 내용 |
|------|------|
| **제목(안)** | OpsClaw: IT 운영 자동화 플랫폼의 설계·구축·운용 25 마일스톤 사례 연구 |
| **영문 제목(안)** | OpsClaw: A 25-Milestone Case Study on Designing, Building, and Operating an IT Operations Automation Platform |
| **핵심 주장** | 25 마일스톤 개발 여정의 설계 결정, 운영 교훈, 비교 실험 |
| **추가 실험 필요** | OpsClaw vs Claude Code(공정 비교), vs Codex, vs CALDERA |
| **대상 학회** | 산업 트랙 (ICSE-SEIP, ASE Industry), 경험 보고 (IEEE Software) |
| **상태** | ⬜ 계획만 완료, 추가 실험 후 본문 작성 |

---

## 작성 현황

| 순서 | 작업 | 상태 |
|------|------|------|
| 1 | Paper 1 전체 (8 섹션) | ✅ 완료 |
| 2 | Paper 2 전체 (8 섹션) | ✅ 완료 |
| 3 | Paper 3 계획 | ✅ 완료 |
| 4 | Paper 3 추가 비교 실험 | ⬜ 미실행 |
| 5 | Paper 3 본문 작성 | ⬜ 실험 후 |

---

## Paper 3 추가 실험 필요 항목

| 실험 | 내용 | 비교 차원 | 상태 |
|------|------|---------|------|
| OpsClaw vs Claude Code (공정) | 양쪽 병렬 허용 | 증적·재현성·추적성 (속도 제외) | ⬜ |
| OpsClaw vs Codex CLI | Codex 환경 구축 | 동일 | ⬜ |
| OpsClaw vs CALDERA | 보안 에뮬레이션 | ATT&CK 커버리지·적응성 | ⬜ |
| Blue Team T2~T4 | 방어 룰 확장 | 탐지 룰 품질·커버리지 | ⬜ |

---

## 핵심 수치 요약

```
[Paper 1 — 아키텍처 검증]
위변조 탐지율:     100% (실험 A)
시간대 불변성:     100% (실험 H, 5 TZ)
상태 전이 차단율:  100% (실험 E)
Playbook 재현율:   100% (실험 G, 10회)
증거 완전율:       100% (실험 C)
병렬 가속:         4.0x (실험 F, N=5)
RL 수렴:           epoch 5 (실험 B)
경험 자동 승급:    20건 (실험 D)

[Paper 2 — 보안/모의해킹]
Red Team:          21/27 (77.8%)
Blue Team:         12/16 (75%)
ATT&CK 커버리지:  17/21 (81%)
Purple Team:       4회전, 취약점 8건, Blue 최종 승리

[Paper 3 — 비교 실험 (예정)]
OpsClaw vs Claude Code: 증적·재현성·추적성 비교 (공정 조건)
OpsClaw vs Codex/CALDERA: TBD
```
