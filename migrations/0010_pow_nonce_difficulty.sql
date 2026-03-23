-- Migration 0010: PoW nonce & difficulty 컬럼 추가
-- nonce 채굴과 target difficulty 제어를 위한 스키마 확장

ALTER TABLE proof_of_work ADD COLUMN IF NOT EXISTS nonce INTEGER NOT NULL DEFAULT 0;
ALTER TABLE proof_of_work ADD COLUMN IF NOT EXISTS difficulty INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN proof_of_work.nonce IS 'Mining nonce — block_hash가 difficulty개 leading zero를 만족하는 값';
COMMENT ON COLUMN proof_of_work.difficulty IS 'Target difficulty — block_hash가 시작해야 하는 leading zero hex 개수';
