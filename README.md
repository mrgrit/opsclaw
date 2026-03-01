# OpsClaw

업무용 A2A 에이전트 오케스트레이션 플랫폼인 OpsClaw의 상세 계획서는 아래 문서를 참고하세요.

- [OpsClaw 상세 계획서 v1.0](docs/opsclaw-plan-v1.0.md)
- [OpsClaw 구현 다음 단계 실행 가이드](docs/implementation-next-steps.md)

## MVP scaffold (시작점)

이번 커밋부터 최소 실행 가능한 Manager/MasterGate 뼈대가 포함됩니다.

### 빠른 실행

```bash
python -m opsclaw.cli --objective "nginx 배포 점검"
python -m opsclaw.cli --objective "Authorization: Bearer token123 on 10.1.0.80" --requires-master
```

### 테스트

```bash
python -m pytest -q
```

## 현재 포함 항목

- `src/opsclaw/orchestrator.py`: Manager 최소 워크플로우
- `src/opsclaw/mastergate.py`: PII/Secret 탐지 + transform/block 판정
- `schemas/a2a/*.json`: A2A 메시지/결과 기본 스키마
- `schemas/audit-log.schema.json`: 감사 로그 기본 스키마
- `docs/adr/0001-mvp-architecture.md`: MVP 아키텍처 ADR
