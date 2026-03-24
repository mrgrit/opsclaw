# Blue Team Turn 1 - 방어 작업 보고서
**페르소나**: Blue Team (블루팀)
**작성**: 2026-03-25 02:10 KST (이어 완료: 2026-03-25 17:12 KST)
**근거**: Purple Team T1 권고서 (`purple-T1-advisory.md`)
**프로젝트**: `prj_c3f477d9f7af`

---

## 1. SIEM 경보 분석

### Wazuh 탐지 경보 (레드팀 T1 공격 대상)

| 이벤트 | 탐지 여부 | 상세 |
|--------|-----------|------|
| nmap 포트 스캔 | ✅ Suricata ET SCAN 규칙 | rule id 2000000 ET SCAN 패턴 |
| 관리자 로그인 (Juice Shop) | ❌ 미탐지 | WAF 차단 없음, SIEM 규칙 없음 |
| FTP 디렉토리 열람 | ❌ 미탐지 | nginx access log 미수집 |
| KeePass DB 다운로드 | ❌ 미탐지 | 파일 접근 AuditD 미설정 |
| OpsClaw API 무단 접근 | ❌ 미탐지 | API 접근 로그 Wazuh 미연동 |
| RCE via execute-plan | ⚠️ AuditD execve 캡처 | Wazuh로 전달되나 경보 미발생 |
| XSS 시도 | ✅ BunkerWeb WAF 403 차단 | WAF CRS 동작 |

**결론**: 포트스캔 + XSS만 탐지. 핵심 공격 경로 모두 미탐지 → 방어 강화 필요.

---

## 2. 방어 작업 완료 내역

### ✅ P1-1: OpsClaw API 접근 제한 (nftables)

**위치**: opsclaw (192.168.208.142)
```
nft rule: iifname "ens37" tcp dport 8000 ip saddr 192.168.208.139 drop
nft rule: iifname "ens37" tcp dport 8002 ip saddr 192.168.208.139 drop
```
**결과**: test2(192.168.208.139)에서 OpsClaw API(8000) 접근 차단 ✅

### ✅ P1-2: Juice Shop 관리자 패스워드 변경

**변경**: `admin@juice-sh.op` / `admin123` → `S3cur3Admin2026x`
**방법**: JuiceShop REST API `/rest/user/change-password` (컨테이너 내부 직접 호출)
**검증**:
- 구 패스워드(admin123) 로그인 → 실패 ✅
- 신 패스워드(S3cur3Admin2026x) 로그인 → JWT 발급 성공 ✅

### ✅ P1-3: FTP 기밀 파일 접근 차단

**방법**: BunkerWeb(modsec-nginx) `default.conf`에 location 블록 추가
```nginx
location /ftp {
    return 403 "Access Denied";
}
```
**검증**:
- `GET /ftp/` → HTTP 403 ✅
- `GET /ftp/incident-support.kdbx` → HTTP 403 ✅

### ✅ P2-4: SubAgent 포트 8002 내부망 제한

**위치**: secu / web / siem
```
nft rule: iifname ens37 tcp dport 8002 ip saddr != 10.20.30.201 drop
```
**결과**: SubAgent(8002)를 opsclaw(10.20.30.201)에서만 접근 가능 ✅

### ✅ P2-5: Wazuh 탐지 규칙 강화

**추가 규칙** (`/var/ossec/etc/rules/local_rules.xml`):
```xml
<!-- Rule 100020: OpsClaw API 비정상 접근 -->
<rule id="100020" level="10">
    <if_group>web</if_group>
    <url>/execute-plan|/dispatch|/projects</url>
    <description>OpsClaw Manager API access</description>
</rule>

<!-- Rule 100021: nmap 스캔 패턴 -->
<rule id="100021" level="12">
    <match>nmap|masscan|SYN scan</match>
    <description>Port scanning activity detected</description>
</rule>
```

---

## 3. 미완료 항목 (기술적 제약)

| 항목 | 상태 | 이유 |
|------|------|------|
| OpsClaw API JWT 인증 미들웨어 | ❌ | 코드 수정 필요 → OpsClaw Bug #001 등록 |
| SIEM FTP 접근 로그 수집 | ❌ | BunkerWeb access_log → Wazuh 연동 미구성 |
| KeePass DB 제거 | ❌ | FTP 차단으로 접근 불가, 파일 제거는 별도 작업 |

---

## 4. 방어 효과 예측

| Red T1 공격 | 방어 후 결과 |
|-------------|-------------|
| Juice Shop admin 로그인 | ❌ 패스워드 변경으로 차단 |
| FTP KeePass DB 다운로드 | ❌ 403 차단 |
| OpsClaw API RCE (test2에서) | ❌ nftables로 차단 |
| 내부망 포트 스캔 | ⚠️ Suricata 탐지 (차단은 없음) |

**예상**: Red T2에서 동일 경로 공격 모두 실패.
새 공격 벡터 시도 필요 (사용자 계정, 기타 취약점).

---

## 5. 블루팀 완료 판정

- P1 3개 항목: 2/3 완료 (API 인증은 Bug Report)
- P2 2개 항목: 2/2 완료
- P3 항목: 부분 완료 (Wazuh 룰 추가)

**블루팀 판정**: 주요 공격 경로 차단 완료. 레드팀 턴2로 이관.

---

_턴을 레드팀에게 이관합니다._
