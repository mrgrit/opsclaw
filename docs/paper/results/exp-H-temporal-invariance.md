# 실험 H 결과: PoW 시간대 불변성

**실행일:** 2026-03-25
**대상:** 최근 10블록, 5개 시간대

## 결과 요약

| 시간대 | 일치율 | 판정 |
|--------|--------|------|
| UTC | 10/10 (100%) | **PASS** |
| Asia/Seoul (+9) | 10/10 (100%) | **PASS** |
| America/Los_Angeles (-7) | 10/10 (100%) | **PASS** |
| Europe/London (0/+1) | 10/10 (100%) | **PASS** |
| Asia/Tokyo (+9) | 10/10 (100%) | **PASS** |

**전체 일치율: 50/50 (100%)**

## 검증 방법

1. DB 세션 timezone을 각 TZ로 변경 (`SET timezone = '...'`)
2. `ts_raw` 필드로 block_hash 재계산: `sha256(prev_hash + evidence_hash + ts_raw + nonce)`
3. 저장된 `block_hash`와 비교

## M27 ts_raw 패치 효과

- M27 이전: psycopg2가 naive datetime 반환 시 +00:00 없이 비교 → 해시 불일치 가능
- M27 이후: `ts_raw` (원본 ISO 문자열) 저장 → timezone 변환 없이 원본 그대로 사용
- **결과:** 어떤 시간대에서도 해시 검증이 100% 성공

## API 검증

```
curl /pow/verify?agent_id=http://localhost:8002
→ valid=True, blocks=111, tampered=0
```

## 결론

OpsClaw PoW 해시 검증은 DB 세션 시간대에 완전히 무관하며, `ts_raw` 기반 해싱으로 시간대 불변성을 보장한다.
