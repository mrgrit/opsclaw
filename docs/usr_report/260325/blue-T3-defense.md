# Blue Team Turn 3 - 방어 작업 보고서
**페르소나**: Blue Team (블루팀)
**작성**: 2026-03-25 17:35 KST
**근거**: Purple Team T3 권고서 (`purple-T3-advisory.md`)
**프로젝트**: `prj_5a0eceb9bff8`

---

## 1. T3 공격 분석

secu의 `oifname ens37 masquerade` 규칙이 test2의 소스 IP를 10.20.30.1로 변환.
opsclaw의 `ip saddr 192.168.208.139` 차단 규칙이 무효화.
**해결책**: secu의 FORWARD 체인에서 masquerade 적용 전에 차단.

---

## 2. 방어 작업 완료 내역

### ✅ P1: secu FORWARD 체인 차단 규칙 추가

**차단 규칙 (secu inet filter forward)**:
```
iifname "ens33" ip saddr 192.168.208.139 ip daddr 10.20.30.201 tcp dport 8000 drop
iifname "ens33" ip saddr 192.168.208.139 ip daddr 10.20.30.201 tcp dport 8002 drop
iifname "ens33" ip saddr 192.168.208.139 ip daddr 10.20.30.100 tcp dport 1514 drop
iifname "ens33" ip saddr 192.168.208.139 ip daddr 10.20.30.100 tcp dport 1515 drop
iifname "ens33" ip saddr 192.168.208.139 ip daddr 10.20.30.100 tcp dport 55000 drop
```

**검증**:
- test2 → `10.20.30.201:8000`: curl exit 124 (timeout) → **BLOCKED ✅**
- secu nftables 저장: `/etc/nftables.conf`

### ✅ P2: siem Wazuh 포트 보호 체인 추가

**추가 체인** (siem `ip wazuh_protect input`):
```
iifname "ens37" tcp dport 1514 ip saddr 192.168.208.139 drop
iifname "ens37" tcp dport 1515 ip saddr 192.168.208.139 drop
iifname "ens37" tcp dport 55000 ip saddr 192.168.208.139 drop
```
*Note: masquerade로 10.20.30.1로 변환되지만, secu FORWARD에서 먼저 차단됨*

---

## 3. 최종 방화벽 구조 (T3 이후)

```
test2 (192.168.208.139) 공격 → secu FORWARD 차단
  → opsclaw:8000/8002 ❌
  → siem:1514/1515/55000 ❌

내부 합법적 트래픽:
  secu(10.20.30.1) → opsclaw:8000 ✅ (정상 동작)
  secu(10.20.30.1) → siem:1514/1515 ✅ (Wazuh 에이전트)
```

---

## 4. 방어 효과 예측

| Red T4 공격 시나리오 | 결과 |
|---------------------|------|
| test2 → OpsClaw 내부 IP | ❌ secu FORWARD 차단 |
| test2 → OpsClaw 외부 IP | ❌ opsclaw ens33 차단 |
| test2 → siem Wazuh API | ❌ secu FORWARD 차단 |
| FTP /ftp/ 접근 | ❌ BunkerWeb 403 |
| JuiceShop admin123 | ❌ 패스워드 변경됨 |

**블루팀 예상**: Red T4에서 기존 경로 모두 차단. 새 공격 벡터 필요.

---

**블루팀 판정**: 방어 체계 대폭 강화. 레드팀 턴 4로 이관.

---

_턴을 레드팀에게 이관합니다._
