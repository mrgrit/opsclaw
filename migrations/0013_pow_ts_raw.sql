-- Migration 0013: PoW 블록체인 ts_raw 컬럼 추가
-- 목적: 채굴 시 사용한 원본 timestamp 문자열을 TEXT로 저장하여
--       verify_chain에서 DB 세션 timezone 설정과 무관하게 동일한 hash를 재계산할 수 있도록 한다.
-- 관련 버그: Bug A — ts 문자열 왕복 변환 불일치 (block_hash_mismatch)

ALTER TABLE proof_of_work ADD COLUMN IF NOT EXISTS ts_raw TEXT;

-- 기존 블록 backfill:
-- TIMESTAMPTZ를 UTC ISO 8601 문자열로 변환 (채굴 당시 generate_proof가 사용한 포맷과 동일)
-- datetime.now(timezone.utc).isoformat() = "YYYY-MM-DDTHH:MM:SS.ffffff+00:00"
UPDATE proof_of_work
SET ts_raw = to_char(ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"+00:00"')
WHERE ts_raw IS NULL;
