# Phase 1: 인프라 구성 완료 보고서
**날짜**: 2026-03-25
**작성**: Master Agent (Claude Code)
**상태**: ✅ 완료 (일부 항목 제약 있음)

---

## 1. 네트워크 재구성

| 서버 | 외부 IF | 내부 IF | 상태 |
|------|---------|---------|------|
| opsclaw | ens33=192.168.208.142 (유지) | ens37=**10.20.30.201** | ✅ IP 변경 완료 |
| secu | ens33=192.168.208.150 (외부차단) | ens37=10.20.30.1 | ✅ SSH/8002 외부차단 |
| web | ens33=비활성화 | ens37=10.20.30.80 | ✅ 외부IF 비활성화 |
| siem | ens33=비활성화 | ens37=10.20.30.100 | ✅ 외부IF 비활성화 |
| test2 | ens33=192.168.208.139 | - | ✅ 공격 서버 (유지) |

- secu: IP forwarding + NAT masquerade (ens33) 설정 → web/siem 인터넷 접근 허용
- web/siem: default gateway = 10.20.30.1 (secu) 경유 인터넷
- INTERNET_OK 확인 완료

## 2. SubAgent 배포 현황

| 서버 | SubAgent URL | 상태 |
|------|-------------|------|
| opsclaw | http://localhost:8002 | ✅ ok |
| secu | http://10.20.30.1:8002 | ✅ ok |
| web | http://10.20.30.80:8002 | ✅ ok |
| siem | http://10.20.30.100:8002 | ✅ ok |
| test2 | http://192.168.208.139:8002 | ✅ ok |

## 3. 보안 도구 설치

### secu
| 도구 | 상태 | 비고 |
|------|------|------|
| nftables | ✅ 기존 운영 중 | 외부 SSH 차단 추가 |
| Suricata IPS | ✅ 운영 중 + 규칙 업데이트 | 49231개 ET 규칙 (18개 신규) |
| AuditD | ✅ 영구 규칙 설정 | execve, connect, setuid 등 모니터링 |
| OSQuery 5.22.1 | ✅ 설치 및 시작 | 프로세스/네트워크/로그인 모니터링 |
| maltrail | ✅ Server 모드 동작 중 (port 8338) | Sensor 모드: pcapy-ng 빌드 실패 |
| Wazuh Agent | ✅ Active | audit.log 수집 추가 |

### web
| 도구 | 상태 |
|------|------|
| BunkerWeb WAF | ✅ 기존 운영 중 |
| AuditD | ✅ 영구 규칙 설정 |
| OSQuery | ✅ 설치 및 시작 |
| Wazuh Agent | ✅ Active + audit.log 수집 추가 |

### siem
| 도구 | 상태 | 비고 |
|------|------|------|
| Wazuh Manager 4.11.2 | ✅ 운영 중 | secu(001), web(002) 에이전트 연결 |
| AuditD | ✅ 설치 | 영구 규칙 설정 |
| OSQuery | ✅ 설치 | |
| SIGMA CLI | ✅ 설치 | pySigma, ES/Splunk 백엔드 |
| SIGMA Rules | ✅ /opt/sigma-rules | SigmaHQ 전체 룰셋 클론 |
| Wazuh 커스텀 규칙 | ✅ 8개 규칙 | 포트스캔, 브루트포스, 권한상승 등 |
| **OpenCTI** | ❌ 건너뜀 | RAM 3.8GB 부족 (최소 16GB 필요) |
| **MISP** | ⚠️ 준비됨 | /opt/misp-docker 준비, 메모리 제약으로 시작 보류 |
| Docker | ✅ 설치됨 | Docker 28.2.2 + Compose v2 |

### opsclaw
| 도구 | 상태 |
|------|------|
| AuditD | ✅ 설치 |
| OSQuery | ✅ 설치 |
| Manager API | ✅ 운영 중 (:8000) |

## 4. test2 공격 도구 (25개 이상)

| # | 도구 | 카테고리 |
|---|------|---------|
| 1 | nmap 7.80 | 포트 스캔 |
| 2 | masscan | 고속 포트 스캔 |
| 3 | nikto | 웹 취약점 스캐너 |
| 4 | sqlmap | SQL 인젝션 |
| 5 | gobuster | 디렉토리/DNS 브루트포스 |
| 6 | ffuf | 퍼즈 테스팅 |
| 7 | hydra | 패스워드 공격 |
| 8 | medusa | 패스워드 공격 |
| 9 | john | 패스워드 크랙 |
| 10 | hashcat | GPU 패스워드 크랙 |
| 11 | netcat | 리버스 쉘 |
| 12 | socat | 소켓 릴레이 |
| 13 | tcpdump | 패킷 캡처 |
| 14 | whatweb | 웹 핑거프린팅 |
| 15 | dirb | 디렉토리 브루트포스 |
| 16 | wfuzz | 퍼즈 테스팅 |
| 17 | smbclient | SMB 클라이언트 |
| 18 | nbtscan | NetBIOS 스캔 |
| 19 | arp-scan | ARP 스캔 |
| 20 | nuclei | 자동 취약점 스캐너 |
| 21 | feroxbuster | 디렉토리 스캐너 |
| 22 | kerbrute | Kerberos 공격 |
| 23 | impacket | Windows 프로토콜 공격 |
| 24 | pwncat-cs | 리버스 쉘 핸들러 |
| 25 | pypykatz | 자격증명 추출 |
| 26 | msfconsole (Metasploit) | 익스플로잇 프레임워크 |
| 27 | Responder (/opt) | NTLMv2 포이즈닝 |

## 5. Wazuh 로그 수집 통합

```
[secu] auditd → /var/log/audit/audit.log → Wazuh Agent → SIEM
[secu] Suricata → /var/log/suricata/eve.json → Wazuh Agent → SIEM
[web] auditd → /var/log/audit/audit.log → Wazuh Agent → SIEM
[web] BunkerWeb → docker logs → Wazuh Agent → SIEM
[siem] Wazuh Manager → 경보 분석 + 커스텀 룰 8개
```

## 6. 제약사항 및 이슈

| 이슈 | 상세 | 조치 |
|------|------|------|
| OpenCTI 미설치 | siem RAM 3.8GB, 최소 16GB 필요 | MISP 대안, Wazuh CTI 통합으로 대체 |
| MISP 미시작 | RAM 부족, Wazuh 2.5GB 사용 중 | /opt/misp-docker 준비됨, 별도 VM 권장 |
| maltrail sensor 모드 불가 | pcapy-ng Ubuntu 22.04 빌드 실패 | Server 모드(HTTP UI) + Suricata ET 규칙 대안 |
| opsclaw Wazuh Agent 미설치 | Control Plane 역할로 우선순위 낮음 | 추후 추가 가능 |

---
**결론**: 핵심 인프라 구성 완료. 보안 모니터링 체계 수립. Red Team 공격 준비 완료.
