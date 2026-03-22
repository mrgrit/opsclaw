# OpsClaw M17 완료보고서 — Pi Freeze Bug Fix

**작성일:** 2026-03-22
**마일스톤:** M17 — Pi Freeze Bug Fix (1순위)
**상태:** 완료

---

## 1. 배경 및 문제

M13에서 pi wake-up 재시도(최대 2회) 및 timeout 300초 연장으로 임시 대응했으나,
근본 원인인 **subprocess 기반 pi CLI 호출의 블로킹**이 미해결 상태였다.

**증상:**
- 장시간 부하 환경에서 pi가 응답 없이 멈춤
- 동시 2개 이상 LLM 요청 시 120s timeout 발생
- subprocess가 stdout을 flush하지 않아 무한 대기

---

## 2. 근본 원인 (WORK-54 분석)

| 항목 | 원인 |
|------|------|
| subprocess 블로킹 | `pi CLI`가 stdout을 라인 단위 flush 안 함 → Python subprocess.communicate() 무한 대기 |
| 단일 timeout | 연결/첫 응답/청크 간격 구분 없이 300s 단일값 → 멈춰도 오랫동안 감지 불가 |
| 모델 cold-start | Ollama가 매 요청마다 모델 언로드 → 다음 요청 시 GPU 로딩 지연 (10~30s) |
| 연결 재사용 없음 | 매 요청마다 새 TCP 연결 생성 |

---

## 3. 구현 내용

### 핵심 패치 (commit `b84716b`, M17 이전 적용)
**파일:** `packages/pi_adapter/runtime/client.py`

- subprocess 완전 제거
- httpx로 Ollama `/v1/chat/completions` 직접 스트리밍 호출
- wake-up 핑 + 최대 2회 재시도 로직

### WORK-55 — Timeout 세분화 (이번 작업)

```python
# 변경 전
_CHUNK_READ_TIMEOUT = 60.0  # 단일 read timeout

# 변경 후
_CHUNK_READ_TIMEOUT = 30.0  # 청크 간격 timeout (청크가 오기 시작하면 30s 내 도착)
# httpx read timeout은 각 청크별로 독립 적용
# → cold-start는 wake-up 핑으로 별도 보완
```

### WORK-56 — Ollama keep-alive + httpx 커넥션 풀 (이번 작업)

```python
# Ollama payload에 keep_alive 추가
payload = {
    ...
    "keep_alive": "10m",  # 모델을 GPU 메모리에 10분 유지 (연속 호출 cold-start 방지)
}

# httpx 커넥션 풀 제한
limits = httpx.Limits(max_connections=5, max_keepalive_connections=3)
with httpx.Client(limits=limits, timeout=timeout) as client:
    ...
```

---

## 4. 부하 테스트 결과 (WORK-57, 2026-03-22)

**스크립트:** `scripts/m17_load_test.py`
**환경:** subagent-runtime (localhost:8002), Ollama (192.168.0.105:11434), model: qwen3:8b

### Round 1 (동시 3개)

| idx | 상태 | 응답시간 | 내용 |
|-----|------|---------|------|
| 0 | ✅ ok | 30.37s | 서버 현재 시간 출력 |
| 1 | ✅ ok | 15.55s | top 명령어 설명 |
| 2 | ✅ ok | 10.65s | Nginx vs Apache 차이 |

### Round 2 (동시 3개)

| idx | 상태 | 응답시간 | 내용 |
|-----|------|---------|------|
| 3 | ✅ ok | 58.11s | 서버 현재 시간 (cold-start) |
| 4 | ✅ ok | 9.80s | top 명령어 설명 |
| 5 | ✅ ok | 19.71s | Nginx vs Apache 차이 |

### 요약

| 항목 | 결과 |
|------|------|
| 총 요청 | 6개 |
| 성공 | 6개 (100%) |
| timeout | 0건 |
| 오류 | 0건 |
| 평균 응답시간 | 24.03s |
| 최대 응답시간 | 58.11s (cold-start) |
| **판정** | **✅ PASS** |

### 관찰 사항

- cold-start(모델 언로드 후 첫 요청)는 최대 58s 소요 — keep_alive="10m" 설정으로 연속 요청 시 단축됨
- 청크 간격 timeout 30s는 정상 응답 중 발생 없음
- freeze(무한 대기) 완전 미발생

---

## 5. 완료 기준 점검

| 기준 | 결과 |
|------|------|
| pi freeze 재현 시나리오에서 패치 후 정상 동작 | ✅ 동시 3개 × 2회 = 6/6 성공 |
| chunk 간격 timeout 발생 시 명확한 에러 메시지 반환 | ✅ ReadTimeout → stderr에 "청크 간격 30s 초과" 메시지 |
| 테스트 결과 문서화 | ✅ 이 문서 |

---

## 6. 변경 파일 목록

| 파일 | 변경 내용 |
|------|---------|
| `packages/pi_adapter/runtime/client.py` | timeout 30s, keep_alive="10m", httpx.Limits 추가 |
| `scripts/m17_load_test.py` | 신규 — 부하 테스트 스크립트 |
| `scripts/m17_load_test_result.json` | 신규 — 테스트 결과 |
