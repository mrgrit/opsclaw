# 보안 실험 종합 결과 — OpsClaw Round

**실행일시:** 2026-03-25 10:02~10:50
**총 소요시간:** ~48분
**OpsClaw 프로젝트:** 5개 (red-t1, red-t2, red-t3, red-t4, blue-t1)

---

## Red Team 종합 점수

| Tier | 내용 | 점수 | 시간 |
|------|------|------|------|
| T1 | 웹앱 공격 (SQLi, XSS, 데이터노출) | **5.5/6** | 12분 |
| T2 | 네트워크 공격 (스캔, ICMP, C2 비콘) | **4.5/6** | 5분 |
| T3 | 권한상승+지속성 (SUID, cron, SSH키) | **6/8** | 5분 |
| T4 | SIEM 우회 (agent 정지, 난독화, syslog 차단) | **5/7** | 5분 |
| **합계** | | **21/27 (77.8%)** | **27분** |

## Blue Team 종합 점수

| 항목 | 결과 |
|------|------|
| 커스텀 탐지 룰 생성 | **7개** (Wazuh 100100~100106) |
| Suricata 시그니처 | **1개** (SQLi sid:1000001) |
| logtest 검증 | **통과** (룰 매칭 확인) |
| 실시간 탐지 | **미완** (agent 버전 불일치) |
| **방어 점수** | **12/16** (룰 생성 완료, 검증 부분적) |

## OpsClaw 하네스 관련 데이터

| 지표 | 값 |
|------|-----|
| PoW 블록 생성 | 프로젝트당 자동 생성 |
| Evidence 기록 | 모든 공격/방어 명령+결과 |
| Playbook 재사용 | 공격 스크립트 Playbook화 가능 |
| 병렬 실행 | Blue 태스크 parallel 활용 |
| 완료 보고서 | 자동 생성 (auto:true) |

## 핵심 발견사항 (보안)

### Critical 발견
1. **web 서버 sudo NOPASSWD ALL** — 일반 사용자가 root 동일 권한
2. **Wazuh Agent 무력화 가능** — sudo로 agent 정지 → SIEM 블라인드
3. **JuiceShop SQLi 토큰 획득** — 관리자 접근, 전체 사용자 목록 노출
4. **Syslog 통신 차단 가능** — iptables로 SIEM 전송 방해

### OpsClaw 실험 우수성
1. **모든 공격/방어가 PoW 블록으로 기록** — 위변조 불가능한 증적
2. **체계적 프로젝트 관리** — Red/Blue 분리, 단계별 lifecycle
3. **병렬 dispatch** — 여러 서버 동시 작업 가능
4. **Playbook 기반 반복** — 동일 공격 시나리오 재실행 1 API call

### OpsClaw 실험 한계
1. **Agent 버전 불일치** — Wazuh agent 4.14.4 > manager, 로그 수집 실패
2. **SubAgent timeout 120초** — 긴 스캔(nmap 전체 포트) 시 timeout
3. **SSH 이스케이핑** — 복잡한 명령은 스크립트 파일로 분리 필요

---

## MITRE ATT&CK 커버리지

| 전술 | 시도 기법 | 성공 | 탐지 룰 |
|------|---------|------|---------|
| Reconnaissance | T1595.002, T1046 | 2/2 | 100104 |
| Initial Access | T1190 | 1/1 | 100100, 100101 |
| Execution | T1059.004, T1059.007 | 1/2 | 100102 |
| Persistence | T1053.003, T1098.004 | 2/2 | (FIM 필요) |
| Privilege Escalation | T1548.001 | 1/1 | (감사 필요) |
| Defense Evasion | T1027, T1070, T1562 | 4/5 | (추가 룰 필요) |
| Discovery | T1046, T1087 | 2/2 | - |
| Lateral Movement | T1021.004 | 0/1 | - |
| Collection | T1005 | 1/1 | 100103, 100105 |
| Exfiltration | T1041, T1048 | 2/2 | - |
| C&C | T1071.001, T1572 | 1/2 | - |
| **합계** | **17 기법** | **17/21 (81%)** | **7 룰** |

---

## 다음 단계

- [ ] Claude Code Only Round (동일 시나리오, 직접 실행)
- [ ] Wazuh Manager 업그레이드 (agent 버전 호환)
- [ ] Blue Team Round 2 (T3, T4 대응 룰 생성)
- [ ] Purple Team 종합 평가
