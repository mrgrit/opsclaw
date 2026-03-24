# Purple Team Turn 3 - 보안 권고서
**페르소나**: Purple Team (퍼플팀)
**작성**: 2026-03-25 17:28 KST
**근거**: Red Team T3 보고서 (`red-T3-attack.md`)

---

## 분석 요약

T3의 핵심 발견: secu가 `oifname ens37 masquerade`를 적용하여
test2 (192.168.208.139)의 소스 IP가 10.20.30.1로 변환됨.
opsclaw의 모든 IP 기반 ACL이 secu 뒤에서 무효화.

**근본 원인**: 경계 방화벽(secu)에서 포워딩 제어 없이 masquerade만 적용.
→ 호스트 방화벽(opsclaw)의 IP 필터가 의미 없어짐.

---

## 우선순위별 보안 권고

### 🔴 P1 - CRITICAL (즉시 조치)

#### 1. secu FORWARD 체인에 test2→opsclaw 차단 추가

- **위험**: secu를 통해 포워딩되는 test2 트래픽이 opsclaw API에 도달
- **권고**:
  ```bash
  # secu forward chain에 test2→opsclaw 차단
  nft add rule inet filter forward \
    iifname ens33 ip saddr 192.168.208.139 \
    ip daddr 10.20.30.201 tcp dport {8000,8002} drop
  ```
- **효과**: 패킷이 masquerade되기 전 secu forward 단계에서 차단

#### 2. secu ens37 masquerade 필요성 재검토

- **현황**: `oifname ens37 masquerade` — 내부망으로 나가는 모든 트래픽 masquerade
- **문제**: 외부 공격자의 소스 IP가 secu IP로 위장되어 호스트 방화벽 우회
- **권고**: masquerade 범위를 내부 서버(web/siem)의 internal 통신에만 적용하거나,
  또는 secu FORWARD 체인에서 외부→내부 신규 연결을 완전 차단
  ```bash
  # 외부망에서 opsclaw 포트로의 신규 연결 차단
  nft add rule inet filter forward \
    iifname ens33 oifname ens37 \
    ip daddr 10.20.30.201 tcp dport {8000,8002} \
    ct state new drop
  ```

---

### 🟡 P2 - HIGH (24시간 내)

#### 3. Wazuh 포트 접근 제한

- **현황**: 1514/1515/55000 포트가 내부망 전체에 노출
- **권고**: siem nftables에 허용 IP 제한
  ```bash
  # siem에서 wazuh 포트를 secu(1514/1515)/opsclaw(55000)만 허용
  nft add rule inet filter input iifname ens37 tcp dport {1514,1515} \
    ip saddr != 10.20.30.1 drop
  nft add rule inet filter input iifname ens37 tcp dport 55000 \
    ip saddr != 10.20.30.201 drop
  ```

---

### 🟢 P3 - MEDIUM

#### 4. 방화벽 기본 정책 강화

- **권고**: secu/siem forward chain 기본 정책을 DROP으로 변경
  ```bash
  nft chain inet filter forward { policy drop; }
  ```
  그리고 허용 규칙만 명시적으로 추가 (whitelist 방식)

#### 5. OpsClaw API 인증 (반복 권고)

- IP 필터만으로는 충분하지 않음 → API Key/JWT 인증이 최후 방어선

---

## 블루팀 작업 지시 (T3)

1. **[즉시]** secu FORWARD 체인: test2→opsclaw:8000/8002 차단 추가
2. **[즉시]** secu FORWARD 외부→내부 신규 연결 제한 (opsclaw 포트만)
3. **[우선]** siem Wazuh 포트 접근 제한
4. **[검토]** secu forward chain 기본 정책 DROP 전환

---

_턴을 블루팀에게 이관합니다._
