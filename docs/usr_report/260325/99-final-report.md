# OpsClaw Purple Team Exercise — Master 종합 보고서
**날짜**: 2026-03-25
**Master Agent**: Claude Code (External Orchestrator)
**플랫폼**: OpsClaw Manager API + SubAgents
**상태**: ✅ 완료 (4회 로테이션, Red T4에서 공격 실패 → 종료)

---

## 1. 실행 요약

| 항목 | 내용 |
|------|------|
| 시작 | 2026-03-25 01:45 KST |
| 종료 | 2026-03-25 17:45 KST |
| 총 소요 | ~16시간 (자율 실행) |
| 로테이션 | T1~T4 (4회) |
| 최종 판정 | **Blue Team 방어 성공** (Red T4 실패) |

---

## 2. 공격/방어 로테이션 결과

| 턴 | 팀 | 결과 | 프로젝트 ID | 핵심 내용 |
|----|----|----|------------|----------|
| T1 | Red | ✅ 승리 | prj_cbf06dd19be1 | 16분 내 3 Critical 달성 |
| T1 | Purple | - | prj_0a5e3c3ba74d | P1-P3 보안 권고 |
| T1 | Blue | ✅ 대응 | prj_c3f477d9f7af | nftables+FTP차단+PW변경 |
| T2 | Red | ✅ 승리 | prj_123f7fa7dfe9 | ens33 외부 IP 우회 RCE |
| T2 | Purple | - | prj_2d379ba0cdde | ens33 차단 + uvicorn rebind |
| T2 | Blue | ✅ 대응 | prj_f0c1afa843dc | ens33 nftables 차단 |
| T3 | Red | ✅ 승리 | prj_b4a5750f92d2 | secu masquerade IP 우회 |
| T3 | Purple | - | prj_89ebd683865c | secu FORWARD 차단 권고 |
| T3 | Blue | ✅ 대응 | prj_5a0eceb9bff8 | secu FORWARD 체인 추가 |
| T4 | Red | ❌ 실패 | prj_6c1736e2278f | 모든 경로 차단, 30분 내 실패 |

---

## 3. 발견된 취약점 전체 목록

### Critical (3개 - T1)

| ID | 취약점 | 위치 | 상태 |
|----|--------|------|------|
| C-01 | JuiceShop 기본 패스워드 admin123 | web:80 | ✅ 수정됨 |
| C-02 | FTP 기밀 파일 무인증 노출 (KeePass DB) | web:80/ftp/ | ✅ 수정됨 |
| C-03 | OpsClaw API 인증 없음 → RCE | opsclaw:8000 | ⚠️ 네트워크 차단 (코드 미수정) |

### High (3개 - T2/T3)

| ID | 취약점 | 위치 | 상태 |
|----|--------|------|------|
| H-01 | opsclaw ens33 외부 IF 미차단 | opsclaw:8000 | ✅ 차단됨 |
| H-02 | secu FORWARD masquerade IP 우회 | secu nftables | ✅ 차단됨 |
| H-03 | Wazuh 포트 내부망 전체 노출 | siem:1514/1515/55000 | ✅ secu FORWARD 차단 |

### Medium (2개)

| ID | 취약점 | 위치 | 상태 |
|----|--------|------|------|
| M-01 | maltrail UI 외부 접근 가능 | secu:8338 | ⚠️ 미수정 (auth 보호) |
| M-02 | OpsClaw PoW 리더보드 IP 노출 | opsclaw:8000/pow/ | ⚠️ 미수정 |

---

## 4. 탐지 현황 최종

| 공격 | Suricata | Wazuh AuditD | WAF |
|------|----------|-------------|-----|
| 포트 스캔 | ✅ ET SCAN | - | - |
| Juice Shop 로그인 | ❌ | ❌ | ❌ |
| FTP 열람 | ❌ | ❌ | ❌ |
| OpsClaw API RCE | ❌ | ⚠️ execve | ❌ |
| XSS | - | - | ✅ WAF 403 |
| nftables 차단 후 접근 시도 | ❌ | ❌ | - |

**탐지 품질 평가**: 낮음. 포트스캔과 XSS만 탐지. 핵심 공격 미탐지.

---

## 5. 방어 체계 최종 상태

### nftables 방화벽 (T4 이후)

```
=== opsclaw (192.168.208.142) ===
INPUT ens33: port 8000/8002 DROP (외부 IF 차단)
INPUT ens37: ip saddr 192.168.208.139 port 8000/8002 DROP

=== secu (192.168.208.150) ===
FORWARD: test2(192.168.208.139)→opsclaw(10.20.30.201) port 8000/8002 DROP
FORWARD: test2(192.168.208.139)→siem(10.20.30.100) port 1514/1515/55000 DROP
INPUT: port 8002 ACCEPT (opsclaw 접근 허용)

=== web (192.168.208.151) ===
(BunkerWeb nginx) location /ftp { return 403; }
SubAgent 8002: 내부망만 허용

=== siem (192.168.208.152) ===
wazuh_protect INPUT: test2→port 1514/1515/55000 DROP
```

### 서비스 변경 사항

| 서비스 | T0 상태 | T4 상태 |
|--------|---------|---------|
| JuiceShop admin | admin123 | S3cur3Admin2026x |
| FTP /ftp/ | HTTP 200 | HTTP 403 |
| OpsClaw API 접근 | 무제한 | 네트워크 차단 (인증 없음) |

---

## 6. OpsClaw 플랫폼 평가

### 강점

1. **execute-plan multi-subagent**: 서버별 다른 subagent_url 지원으로 멀티 서버 병렬 작업
2. **PoW 증거 체계**: 각 task 실행 시 자동 PoW 블록 생성 → 감사 추적 용이
3. **External Master Mode**: Claude Code가 직접 오케스트레이션 가능, 유연한 워크플로
4. **프로젝트 라이프사이클**: intake→plan→execute→completion-report 구조로 작업 추적

### 약점 / 개선 필요

1. **API 인증 없음** (Critical Bug): execute-plan이 인증 없이 호출 가능 → RCE
2. **PoW 리더보드 내부 IP 노출**: `/pow/leaderboard`에 에이전트 IP 노출
3. **execute-plan 응답 지연**: 긴 명령은 timeout, 결과 빈 반환
4. **JSON 파싱 이슈**: 복잡한 명령어 인라인 전달 시 특수문자 파싱 오류

### 버그 리포트 (Blue Team 제기)

| 버그 ID | 내용 | 우선순위 |
|---------|------|---------|
| BUG-001 | Manager API 인증 미들웨어 없음 | Critical |
| BUG-002 | PoW 리더보드 IP 주소 공개 | Medium |

---

## 7. 시사점 및 학습

### 방화벽 설계 교훈

1. **단일 인터페이스 차단의 한계**: ens37만 차단 → ens33으로 우회
2. **NAT masquerade와 IP 필터의 충돌**: secu ens37 masquerade가 소스 IP를 변조하여 호스트 방화벽 우회
3. **경계 방화벽(secu)에서의 차단이 핵심**: 호스트 방화벽보다 경계에서 차단이 효과적
4. **기본 정책 DROP**: 명시적 허용이 아니면 기본 DROP (whitelist 방식)

### 보안 아키텍처 권장 사항

1. OpsClaw Manager API → 인증 미들웨어 추가 (최고 우선순위)
2. OpsClaw uvicorn → `--host 10.20.30.201` 또는 `127.0.0.1` 바인딩
3. secu forward chain → 기본 정책 DROP + whitelist 방식으로 전환
4. SIEM 로그 수집 강화 → nginx access log, API 접근 로그 추가

---

## 8. 탐지 체계 개선 권고

### 즉시 추가 필요 규칙

```yaml
# Wazuh 룰 추가 권고
- rule 100025: POST /projects + /execute-plan → OpsClaw API 공격 시도
- rule 100026: FTP directory listing attempt (nginx 403 반복)
- rule 100027: JuiceShop /rest/user/login 실패 패턴 (브루트포스)
- rule 100028: nftables DROP 패킷 (firewalld audit)
```

### 로그 수집 미비 항목

- OpsClaw Manager API access log (Wazuh Agent 미설치)
- web nginx access log (BunkerWeb container)
- JuiceShop application log

---

## 9. 최종 판정

| 항목 | 판정 |
|------|------|
| 레드팀 목표 (30분 내 Critical 달성) | T1-T3 달성, T4 실패 |
| 블루팀 목표 (모든 경로 차단) | T4에서 달성 |
| **최종 승자** | **블루팀 승리** (4턴 만에 모든 경로 차단) |

**총평**: 레드팀이 T1~T3에서 3가지 다른 우회 경로를 발견했지만, 블루팀이 매 턴 빠르게 대응하여 T4에서 완전한 방어 달성. OpsClaw API 인증 부재가 유일하게 해결되지 않은 근본 취약점.

---

## 10. 다음 단계 권고

1. **[Critical]** OpsClaw API 인증 미들웨어 구현 (M28 제안)
2. **[High]** secu forward chain 기본 DROP 정책으로 전환
3. **[High]** SIEM 탐지 규칙 대폭 강화 (API 접근, 로그인 시도 등)
4. **[Medium]** maltrail port 8338 secu INPUT 규칙 추가
5. **[Low]** OpsClaw PoW 리더보드 IP 노출 수정

---

_Master Agent: Claude Code_
_보고서 완료: 2026-03-25 17:45 KST_
