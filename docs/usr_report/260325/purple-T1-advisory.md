# Purple Team Turn 1 - 보안 권고서
**페르소나**: Purple Team (퍼플팀)
**작성**: 2026-03-25 02:02 KST
**근거**: Red Team T1 보고서 (`red-T1-attack.md`)

---

## 분석 요약

레드팀이 16분 내 3개 Critical 취약점으로 내부망 완전 침투 달성.
공격 경로: `외부(test2) → Juice Shop(기본패스워드) → FTP(기밀파일) → OpsClaw API(RCE) → secu 명령실행`

**핵심 문제**: OpsClaw Manager API가 인증 없이 내부망에서 완전 접근 가능.
이로 인해 내부망 접근 권한만 있으면 모든 SubAgent 서버에 임의 명령 실행 가능.

---

## 우선순위별 보안 권고

### 🔴 P1 - CRITICAL (즉시 조치 필요)

#### 1. OpsClaw API 인증 추가
- **위험**: 인증 없는 API로 내부망 전체 RCE 가능
- **권고**:
  - Manager API에 JWT 또는 API Key 인증 미들웨어 추가
  - IP Allowlist: 10.20.30.201 (opsclaw)만 허용
  - SubAgent(8002) 포트를 내부망으로만 제한 (nftables INPUT 규칙)
- **예시 설정 (nftables)**:
  ```
  nft add rule ip filter INPUT iifname ens37 tcp dport 8000 ip saddr != 10.20.30.201 drop
  nft add rule ip filter INPUT iifname ens37 tcp dport 8002 ip saddr != 10.20.30.201 drop
  ```

#### 2. Juice Shop 기본 패스워드 변경
- **위험**: admin123 기본 패스워드 → 관리자 계정 즉시 탈취 가능
- **권고**:
  - 관리자 패스워드 즉시 변경
  - 강력한 패스워드 정책 적용 (12자 이상, 특수문자 포함)
  - MFA 고려

#### 3. FTP 디렉토리 접근 제어
- **위험**: KeePass DB, 기밀 M&A 문서 외부 접근 가능
- **권고**:
  - `/ftp/` 디렉토리 외부 접근 차단 (WAF 규칙)
  - 민감 파일 (*.kdbx, *acquisitions*, *.bak) 즉시 제거 또는 이동
  - Directory listing 비활성화

---

### 🟡 P2 - HIGH (24시간 내 조치)

#### 4. 내부망 서비스 포트 제한
- **위험**: 8000, 8002 포트가 내부망 전체에 노출
- **권고**:
  - opsclaw:8000 → 10.20.30.201 자체 + 관리자 IP만 허용
  - SubAgent:8002 → opsclaw(10.20.30.201)에서만 접근 허용
  - secu nftables에 내부망 서비스 방화벽 추가

#### 5. BunkerWeb WAF 강화
- **현황**: XSS 피드백 POST 차단 (403) → WAF 정상 동작 중
- **권고**:
  - OWASP ModSecurity Core Rule Set (CRS) 활성화 확인
  - FTP 경로 차단 규칙 추가
  - Admin API 경로 (/api/Users, /api/Orders 등) WAF 필터링

#### 6. Juice Shop 사용자 데이터 보호
- **위험**: 관리자 API로 전체 사용자 데이터 조회 가능
- **권고**:
  - API 응답에서 password_hash 필드 제거
  - RBAC 적용: 관리자 API는 관리자 IP에서만
  - Rate limiting 적용

---

### 🟢 P3 - MEDIUM (1주일 내)

#### 7. SIEM 모니터링 규칙 강화
- 추가 권장 탐지 규칙:
  - OpsClaw API 비정상 프로젝트 생성 급증
  - Juice Shop 로그인 실패 패턴
  - FTP 디렉토리 접근 로그
  - 내부망 포트 스캔 (nmap/masscan 특성 패턴)

#### 8. 네트워크 세그멘테이션 강화
- test2(192.168.208.139)는 내부망(10.20.30.x)에 직접 라우팅 불가하도록
- secu nftables에서 외부망→내부망 포워딩 제한

#### 9. KeePass DB 분석
- 다운로드된 incident-support.kdbx 패스워드 변경
- KeePass DB를 공개 웹에서 제거

---

## 탐지 현황 분석

| 공격 | Suricata 탐지 | Wazuh AuditD 탐지 | WAF 차단 |
|------|-------------|------------------|---------|
| 포트 스캔 | ✅ ET SCAN 규칙 | - | - |
| 관리자 로그인 | ❌ 탐지 안됨 | ❌ | ❌ |
| FTP 열람 | ❌ | ❌ | ❌ |
| KeePass DB 다운로드 | ❌ | ❌ | ❌ |
| OpsClaw API 접근 | ❌ | ❌ | ❌ |
| RCE via API | ❌ | ⚠️ (execve 캡처) | ❌ |
| XSS 시도 | ❌ | ❌ | ✅ WAF 차단 |

**결론**: 실제 공격의 대부분이 탐지되지 않음. 탐지 체계 전면 강화 필요.

---

## 블루팀 작업 지시

1. **[즉시]** OpsClaw API 접근 제한 (nftables)
2. **[즉시]** Juice Shop 관리자 패스워드 변경
3. **[즉시]** FTP 기밀 파일 제거/차단
4. **[우선]** Wazuh에 API 접근 모니터링 규칙 추가
5. **[우선]** BunkerWeb에 FTP 경로 차단 규칙 추가
6. **[검토]** OpsClaw에 인증 미들웨어 추가 (OpsClaw Bug로 보고)

---

_턴을 블루팀에게 이관합니다._
