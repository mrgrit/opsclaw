# Red Team Turn 2 - 공격 보고서
**페르소나**: Red Team (레드팀)
**시작**: 2026-03-25 02:11 KST
**종료**: 2026-03-25 17:15 KST
**공격 서버**: test2 (192.168.208.139)
**공격 대상**: 10.20.30.0/24 내부망

---

## T1 방어 효과 검증

| 방어 항목 | 우회 결과 |
|-----------|-----------|
| nftables ens37 차단 (test2→opsclaw 내부IP) | ✅ 차단 됨 (`10.20.30.201:8000` 차단) |
| FTP `/ftp/` BunkerWeb 403 | ✅ 차단 됨 (KeePass DB 접근 불가) |
| JuiceShop admin123 패스워드 | ✅ 차단 됨 (로그인 실패) |
| SubAgent 8002 내부망 제한 | ✅ 직접 접근 차단 됨 |

---

## 취약점 발견 및 공격 성공 내역

### 🔴 CRITICAL-T2: nftables 방화벽 우회 — 외부 IP 경유 RCE

- **위치**: `http://192.168.208.142:8000` (opsclaw 외부 인터페이스)
- **취약점**: T1 방어가 `ens37` (내부망 IF)만 차단, `ens33` (외부 IF) 미차단
- **공격 경로**:
  1. `POST /projects` → 프로젝트 생성 via **192.168.208.142:8000** (무인증)
  2. `/plan` → `/execute` stage 전환
  3. `POST /execute-plan` → secu SubAgent(`10.20.30.1:8002`)로 명령 전달
- **실행 명령**: `id; hostname; echo OPSCLAW_BYPASS_SUCCESS`
- **결과**:
  ```
  uid=1000(secu) gid=1000(secu) groups=1000(secu),4(adm),24(cdrom),27(sudo)...
  secu
  OPSCLAW_BYPASS_SUCCESS
  ```
- **영향**: T1 방어 우회. secu 서버 완전 장악. 내부망 서버 모두 접근 가능.
- **프로젝트 ID**: `prj_05e2b0ca5ef9`

**근본 원인**:
```
opsclaw 방화벽:
- ens37 (10.20.30.201): 192.168.208.139 차단 ✅
- ens33 (192.168.208.142): 규칙 없음 ❌
test2와 opsclaw가 동일 192.168.208.x 서브넷 → 직접 접근 가능
```

---

### 🟢 확인 사항: T1 방어 유효 항목

#### FTP 차단 (T2에서 우회 시도 실패)
- `/ftp/` → HTTP 403 ✅
- `/ftp/incident-support.kdbx` → HTTP 403 ✅
- `/ftp/acquisitions.md` → HTTP 403 ✅

#### JuiceShop admin123 우회 시도 실패
- `admin@juice-sh.op / admin123` → 로그인 실패 ✅
- SQL 인젝션 bypass → WAF 차단 또는 JuiceShop 자체 필터 ✅

---

### 🟡 MEDIUM-T2: JuiceShop 미인증 관리자 페이지 노출

- **위치**: `http://10.20.30.80/administration`
- **결과**: HTTP 200 반환 (클라이언트 SPA 라우팅)
- **영향**: 관리자 메뉴 URL 노출 (서버 인증은 API 레벨에서 처리)

---

## 실패한 공격

| 공격 | 결과 | 이유 |
|------|------|------|
| FTP 기밀 파일 다운로드 | ❌ 실패 | BunkerWeb location /ftp { 403 } |
| JuiceShop admin123 로그인 | ❌ 실패 | 패스워드 변경됨 |
| SubAgent 8002 직접 접근 | ❌ 실패 | nftables 내부망 제한 |
| JuiceShop /api/Users 무인증 | ❌ 실패 | 토큰 인증 필요 |

---

## 요약 (레드팀 판정: 공격 성공)

**T1 방어 우회**: nftables 방화벽 단일 IF 차단 취약점 → 외부 IP 경유 RCE 재달성

**핵심 문제**: OpsClaw API가 두 개 네트워크 인터페이스에 노출 (0.0.0.0:8000).
방어팀이 내부망(ens37)만 차단하고 외부망(ens33) 미차단.

---

_턴을 퍼플팀에게 이관합니다._
