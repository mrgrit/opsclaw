# DGX Spark SubAgent 설치 보고서

**날짜:** 2026-03-26
**서버:** DGX Spark (192.168.0.105)
**계정:** mrgrit
**상태:** ✅ 완료

## 서버 스펙

| 항목 | 값 |
|------|-----|
| 호스트명 | spark-1397 |
| OS | Ubuntu, Linux 6.17.0-1008-nvidia (aarch64) |
| GPU | NVIDIA DGX Spark |
| VRAM | 128GB |
| SSD | 3.6TB NVMe (/dev/nvme0n1p2) |
| RAM | 119GB |
| Python | 3.12.3 |
| Ollama | http://localhost:11434 (20개 모델) |

## 설치 내역

1. **git clone** — `https://github.com/mrgrit/opsclaw.git` → `/home/mrgrit/opsclaw/`
2. **Python venv** — `.venv/` (fastapi, pydantic, uvicorn, httpx)
3. **SubAgent 기동** — `uvicorn apps.subagent-runtime.src.main:app --host 0.0.0.0 --port 8002`
4. **로컬 지식** — `data/local_knowledge/dgx-spark.json` (GPU/Ollama 특화)

## 검증 결과

| 테스트 | 결과 |
|--------|------|
| /health | ✅ OK |
| /capabilities | ✅ 8개 capability |
| /a2a/mission (gemma3:12b) | ✅ 2 step 자율 실행 (uname, nvidia-smi) |
| Manager dispatch (3 tasks parallel) | ✅ 3/3 성공 |

## SubAgent URL
```
http://192.168.0.105:8002
```

## 비고
- Ollama가 localhost에서 실행되므로 LLM invoke_llm/analyze 직접 호출 가능
- aarch64 아키텍처이므로 일부 바이너리 호환 주의
- 향후 파인튜닝 실험(Paper 5)의 학습/추론 서버로 활용 예정
