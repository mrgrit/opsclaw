# 실험 D 결과: 경험 재활용 효과 (A/B 테스트)

**실행일:** 2026-03-25

## 결과 요약

| 지표 | A (no context) | B (project context) | 차이 | 판정 |
|------|---------------|--------------------|----|------|
| 응답 길이 | 1,348자 | **2,040자** | +51% | **B 우위** |
| 명령어 구체성 | 3개 (df, du, rm) | **6개** (df, du, rm, find, ncdu, sudo) | +100% | **B 우위** |
| RAG 참조 | 0건 | 0건 | - | FTS 적중 없음 |
| 자동 승급 | - | 20건 (전부 [Auto]) | - | **정상 동작** |

## Phase 1: 자동 경험 승급 결과

- **총 experience: 20건**, 전부 `[Auto]` 접두어 — `auto_promote_high_reward()` 정상 동작
- avg_reward ≥ 1.1 프로젝트 모두 자동 승급됨
- category: 전부 "operations" (기본값)

## Phase 2: A/B 비교 분석

### A그룹 (context 없음)
- 일반적인 디스크 관리 설명
- `df -h`, `du -sh`, `rm` 3개 명령어만 언급

### B그룹 (project context 주입)
- 프로젝트 evidence 참조하여 더 구체적 답변
- `df -h`, `du -sh`, `rm`, `find`, `ncdu`, `sudo` 6개 명령어
- 실제 실행 컨텍스트 기반으로 단계별 절차 제시

### RAG 적중 0건 원인
- FTS 인덱스에 "디스크" 키워드가 한국어로 저장되지 않음 (영문 FTS 기반)
- **개선 필요:** 한국어 FTS 또는 trigram 인덱스 추가

## 발견사항

| 항목 | 내용 | 심각도 |
|------|------|--------|
| **자동 승급 정상** | 20건 모두 자동 승급 | 우수 |
| **직접 context > RAG** | evidence/report 직접 참조가 RAG보다 효과적 | 참고 |
| **한국어 FTS 미지원** | retrieval_documents FTS가 영문 기반 → 한국어 쿼리 적중 0 | 개선 필요 |
| **context 주입 효과** | 51% 길이 증가, 100% 명령어 다양성 증가 | 우수 |

## OpsClaw 위임 준수 점검

모든 API 호출은 `POST /chat`, `GET /experience`, `GET /projects` — OpsClaw API 경유. ✅
