# Red Team Turn 3 - 공격 보고서
**페르소나**: Red Team (레드팀)
**시작**: 2026-03-25 17:15 KST
**종료**: 2026-03-25 17:25 KST
**공격 서버**: test2 (192.168.208.139)
**공격 대상**: 10.20.30.0/24 내부망

---

## T2 방어 효과 검증

| 방어 항목 | 우회 결과 |
|-----------|-----------|
| nftables ens33 차단 (opsclaw 외부 IP) | ✅ 차단 확인 (Connection timed out) |
| nftables ens37 차단 (opsclaw 내부 IP) | ❌ **우회 성공** |

---

## 취약점 발견 및 공격 성공 내역

### 🔴 CRITICAL-T3: secu NAT Masquerade로 IP 필터 우회

- **위치**: `http://10.20.30.201:8000` (opsclaw 내부망 IP)
- **취약점**: secu nftables에 `oifname ens37 masquerade` 규칙 존재
- **공격 원리**:
  ```
  test2 (192.168.208.139) → secu ens33 → 내부망 포워딩
                                           ↓
                            secu POSTROUTING: oifname ens37 masquerade
                                           ↓
  opsclaw ens37에서 보이는 소스 IP: 10.20.30.1 (secu)
                                           ↓
  opsclaw nftables: ip saddr 192.168.208.139 → 매칭 안됨 → 통과!
  ```
- **결과**:
  - `http://10.20.30.201:8000/projects` → 50개 프로젝트 조회 성공
  - execute-plan으로 RCE 가능 (T2에서 이미 실증)
- **영향**: T1/T2 방어 모두 우회. secu 포워딩 차단이 근본 해결책.

---

### 🟡 MEDIUM-T3: Wazuh 포트 내부망 노출

- **위치**: `10.20.30.100` (siem)
- **노출 포트**:
  - 1514/tcp: Wazuh 에이전트 통신
  - 1515/tcp: Wazuh 에이전트 등록
  - 55000/tcp: Wazuh Manager API
- **공격 가능성**:
  - 1515: 로그 에이전트 등록 → 허위 경보 주입 가능
  - 55000: Wazuh API 무차별 대입 공격 가능
  - 기본 자격증명 시도 필요

---

## 실패한 공격

| 공격 | 결과 | 이유 |
|------|------|------|
| OpsClaw 외부 IP(192.168.208.142) | ❌ 실패 | ens33 nftables 차단 유효 |
| JuiceShop SQL injection in search | ❌ 차단 | BunkerWeb WAF 또는 JuiceShop 필터 |
| JuiceShop 패스워드 리셋 (보안 질문) | ❌ 차단 | 잘못된 답 |
| Wazuh API 기본 자격증명 | ❌ (미완료) | 쉘 파싱 오류 |

---

## 요약 (레드팀 판정: 공격 성공)

**secu NAT masquerade를 통한 IP 필터 우회**:
opsclaw의 IP 기반 ACL이 secu의 masquerade로 완전히 무력화.
네트워크 경계 방어는 **포워딩 차단** 없이는 무의미함.

---

_턴을 퍼플팀에게 이관합니다._
