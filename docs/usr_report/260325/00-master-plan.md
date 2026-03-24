# OpsClaw Purple Team Exercise — Master Plan
**날짜**: 2026-03-25
**Master Agent**: Claude Code (External Orchestrator)
**플랫폼**: OpsClaw Manager API + SubAgents

---

## 보고서 네이밍 규칙

```
docs/usr_report/260325/
├── 00-master-plan.md              # 이 파일 (전체 계획)
├── 01-infra-setup.md              # 인프라 구성 완료 보고서
├── red-T1-attack.md               # 레드팀 턴 1 공격 보고서
├── purple-T1-advisory.md          # 퍼플팀 턴 1 보안 권고
├── blue-T1-defense.md             # 블루팀 턴 1 방어 작업
├── red-T2-attack.md               # ...반복 (최대 T5)
├── purple-T2-advisory.md
├── blue-T2-defense.md
└── 99-final-report.md             # Master 종합 보고서
```

---

## 작업 단계

### Phase 0: 하드웨어 자원 제안 (지금)
→ 사용자 확인 후 시작

### Phase 1: 인프라 구성
- opsclaw 내부망 IP 설정 (10.20.30.201)
- 외부 인터페이스 비활성화 (opsclaw NAT 제외)
- OSQuery + AuditD + Sysmon 설치/룰/SIEM 연동
- Siem: OpenCTI + MISP + SIGMA 설치
- secu: maltrail 설치
- kali: 20개 이상 모의해킹 도구 설치 + subagent

### Phase 2~6: 레드/퍼플/블루 로테이션 (최대 5회)
- 레드: 내부망 모의해킹 (30분), 보고서, 턴 이관
- 퍼플: 보안 권고서 작성, 턴 이관
- 블루: SIEM 분석 + 방어 작업, 보고서, 턴 이관
- 종료 조건: 30분간 공격 실패 또는 5회 로테이션

### Phase 7: Master 종합 보고서

---

## 서버 구성

| 서버 | 외부 IP | 내부 IP | 역할 | SubAgent |
|------|---------|---------|------|----------|
| opsclaw | 192.168.208.142 | 10.20.30.201 | Control Plane | http://localhost:8002 |
| secu | 192.168.208.150 | 10.20.30.1 | Firewall/IPS | http://192.168.208.150:8002 |
| web | 192.168.208.151 | 10.20.30.80 | WAF/Web | http://192.168.208.151:8002 |
| siem | 192.168.208.152 | 10.20.30.100 | SIEM | http://192.168.208.152:8002 |
| kali | TBD | TBD | 레드팀 | TBD |

---

## 위임 원칙

- Claude Code = 계획/분할/위임/검수/개입
- 모든 실행 = Manager API execute-plan → SubAgent
- 직접 SSH 금지 (스크립트 배포 제외)
- 각 Phase 완료 후 completion-report + PoW 기록

---

## 진행 상태

| Phase | 상태 |
|-------|------|
| Phase 0: 자원 제안 | ✅ 완료 |
| Phase 1: 인프라 | ✅ 완료 |
| Phase 2~5: 레드/퍼플/블루 (T1~T4) | ✅ 완료 (4회, T4에서 블루팀 승리) |
| Phase 7: Master 종합 보고서 | ✅ 완료 (`99-final-report.md`) |

## 최종 결과

- **블루팀 승리**: Red T4에서 30분 내 Critical 공격 실패
- **발견 취약점**: 3 Critical, 3 High, 2 Medium
- **미해결**: OpsClaw API 인증 없음 (BUG-001)
- **보고서**: `docs/usr_report/260325/` 전체
