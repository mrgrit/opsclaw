# Blue Team Turn 2 - 방어 작업 보고서
**페르소나**: Blue Team (블루팀)
**작성**: 2026-03-25 17:20 KST
**근거**: Purple Team T2 권고서 (`purple-T2-advisory.md`)
**프로젝트**: `prj_f0c1afa843dc`

---

## 1. T2 공격 분석

레드팀이 T1 nftables 방어를 우회:
- T1 방어: `ens37` (내부망 IF)의 192.168.208.139 차단
- 우회 경로: `ens33` (외부망 IF) 192.168.208.142:8000 → 직접 접근

opsclaw와 test2가 동일 서브넷(192.168.208.x) 위에 있어 외부 IP 직접 접근 가능.

---

## 2. 방어 작업 완료 내역

### ✅ P1: nftables ens33 외부 IF 차단

```bash
nft add rule ip filter INPUT iifname ens33 tcp dport 8000 drop
nft add rule ip filter INPUT iifname ens33 tcp dport 8002 drop
```

**검증**:
- test2 → `192.168.208.142:8000`: curl exit 28 (timeout) → **차단 ✅**
- secu → `10.20.30.201:8000`: curl exit 0 → **내부망 정상 접근 ✅**
- nftables 규칙 `/etc/nftables.conf` 저장

**현재 opsclaw nftables 규칙 전체**:
```
ens37: 192.168.208.139 → port 8000 DROP
ens37: 192.168.208.139 → port 8002 DROP
ens33: any → port 8000 DROP
ens33: any → port 8002 DROP
```

---

## 3. 미완료 항목

| 항목 | 상태 | 이유 |
|------|------|------|
| OpsClaw uvicorn --host 10.20.30.201 rebind | ❌ | 서비스 재시작 필요, Manager API 운영 중 |
| OpsClaw Wazuh Agent 설치 | ❌ | Control plane 역할 우선순위 낮음 |
| API Key 인증 미들웨어 | ❌ | 코드 수정 필요 → Bug Report 유지 |

---

## 4. 방어 효과 예측

| 공격 시나리오 | 방어 후 |
|--------------|---------|
| test2 → OpsClaw 내부IP(10.20.30.201) | ❌ ens37 + saddr 차단 |
| test2 → OpsClaw 외부IP(192.168.208.142) | ❌ ens33 전체 차단 |
| secu/web/siem SubAgent 직접 접근 | ❌ ens37 non-opsclaw 차단 |
| 내부망에서 API 정상 접근 | ✅ 10.20.30.201 → localhost 정상 |

---

**블루팀 판정**: 외부 경로 차단 완료. 레드팀 턴 3으로 이관.

---

_턴을 레드팀에게 이관합니다._
