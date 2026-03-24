# Purple Team Turn 2 - 보안 권고서
**페르소나**: Purple Team (퍼플팀)
**작성**: 2026-03-25 17:15 KST
**근거**: Red Team T2 보고서 (`red-T2-attack.md`)

---

## 분석 요약

블루팀 T1 방어는 내부망(ens37) 차단만 구현. 공격자가 외부망(ens33) 경로로 우회 성공.
**근본 원인**: OpsClaw API가 `0.0.0.0:8000`에 바인딩되어 모든 인터페이스에 노출.
nftables를 한 인터페이스만 차단하면 나머지 인터페이스로 우회 가능.

---

## 우선순위별 보안 권고

### 🔴 P1 - CRITICAL (즉시 조치)

#### 1. OpsClaw API 외부 인터페이스 차단

- **위험**: `192.168.208.142:8000` (ens33) 외부망 접근 가능 → test2가 직접 RCE
- **권고**:
  - Option A: nftables에 ens33 차단 규칙 추가
    ```bash
    nft add rule ip filter INPUT iifname ens33 tcp dport 8000 drop
    nft add rule ip filter INPUT iifname ens33 tcp dport 8002 drop
    ```
  - Option B: Manager API를 `127.0.0.1:8000`으로 rebind (내부 접근만 허용)
    - 단, secu/web/siem SubAgent에서 opsclaw API 접근이 필요하면 `10.20.30.201`만 허용
  - **권장**: Option A (즉시 적용 가능) + 추후 Option B (근본 해결)

---

### 🟡 P2 - HIGH (24시간 내)

#### 2. OpsClaw API 인증 구현

- **위험**: 인증 없이 누구나 프로젝트 생성 및 execute-plan으로 RCE 가능
- **권고**:
  - API Key 헤더 인증 (최소 요건)
  - 또는 IP Allowlist를 완전히 신뢰할 수 없으므로 인증 추가 필요
  - **OpsClaw Bug Report** 등록 필요

#### 3. OpsClaw 서비스 바인딩 변경

- **현황**: `uvicorn --host 0.0.0.0 --port 8000` → 모든 인터페이스 노출
- **권고**: `--host 10.20.30.201` 또는 `127.0.0.1`로 제한

---

### 🟢 P3 - MEDIUM (1주일 내)

#### 4. JuiceShop 관리자 페이지 추가 보호

- `/administration` URL은 클라이언트 라우팅으로 200 반환
- **권고**: WAF에서 `/administration` 경로 토큰 검증 미들웨어 추가

#### 5. 방화벽 규칙 전수 감사

- 현재 nftables 규칙이 인터페이스별로 불완전
- 모든 서비스 포트에 대해 허용 IP 목록 재검토
- 기본 정책을 DROP으로 설정하고 화이트리스트 방식으로 전환

---

## 탐지 현황 업데이트 (T2)

| 공격 | 탐지 |
|------|------|
| 외부 IP 경유 OpsClaw API 접근 | ❌ (opsclaw Wazuh Agent 미설치) |
| execute-plan RCE (secu에서) | ⚠️ AuditD execve 캡처 (경보 미발생) |

**권고**: opsclaw에 Wazuh Agent 설치 + Manager API 접근 로그 수집

---

## 블루팀 작업 지시 (T2)

1. **[즉시]** nftables에 ens33 차단 규칙 추가 (OpsClaw + SubAgent)
2. **[우선]** OpsClaw uvicorn 바인딩 10.20.30.201로 변경 (재시작 필요)
3. **[검토]** OpsClaw Wazuh Agent 설치 (API 접근 모니터링)

---

_턴을 블루팀에게 이관합니다._
