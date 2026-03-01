# OpsClaw

업무용 A2A 에이전트 오케스트레이션 플랫폼인 OpsClaw의 상세 계획서는 아래 문서를 참고하세요.

- [OpsClaw 상세 계획서 v1.0](docs/opsclaw-plan-v1.0.md)
- [OpsClaw 구현 다음 단계 실행 가이드](docs/implementation-next-steps.md)

## MVP scaffold (시작점)

## 설치 (Linux)

```bash
python3 -m pip install --user .
# 개발 모드가 필요하면(환경에 따라 실패 가능)
python3 -m pip install --user -e .
```

> `opsclaw: command not found`가 뜨면 `~/.local/bin`을 PATH에 추가하세요.

```bash
export PATH="$HOME/.local/bin:$PATH"
```

이번 커밋부터 최소 실행 가능한 Manager/MasterGate 뼈대가 포함됩니다.

### 빠른 실행 (Linux)

```bash
PYTHONPATH=src python3 -m opsclaw.cli --objective "nginx 배포 점검"
PYTHONPATH=src python3 -m opsclaw.cli --objective "Authorization: Bearer token123 on 10.1.0.80" --requires-master
```

### 의존성 선설치 단계 포함 실행

```bash
PYTHONPATH=src python3 -m opsclaw.cli --objective "초기 점검 작업" --install-deps
```

- `--install-deps` 옵션은 작업 dispatch 전에 아래 bootstrap을 실행합니다.
  - `python3 -m pip install --upgrade pip`
  - `requirements.txt`가 있으면 `python3 -m pip install -r requirements.txt`

### 테스트

```bash
PYTHONPATH=src python3 -m pytest -q
```

## 현재 포함 항목

- `src/opsclaw/orchestrator.py`: Manager 최소 워크플로우 + SubAgent/StateStore 연동
- `src/opsclaw/subagent.py`: 로컬 SubAgent 실행기(쉘 명령 실행/수집 + 위험 명령 Guardrails)
- `src/opsclaw/state_store.py`: JSON 기반 작업 상태 저장
- `src/opsclaw/mastergate.py`: PII/Secret 탐지 + transform/block 판정
- `src/opsclaw/a2a.py`: A2A RUN_SCRIPT/STATUS_UPDATE 메시지 생성
- `src/opsclaw/audit.py`: 감사 로그(audit log) append 저장
- `schemas/a2a/*.json`: A2A 메시지/결과 기본 스키마
- `schemas/audit-log.schema.json`: 감사 로그 기본 스키마
- `docs/adr/0001-mvp-architecture.md`: MVP 아키텍처 ADR
