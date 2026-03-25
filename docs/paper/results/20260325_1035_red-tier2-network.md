# Red Team Tier 2 결과: 네트워크/IPS 우회 공격

**실행일시:** 2026-03-25 10:30~10:35
**OpsClaw 프로젝트:** red-tier2-network-attack

## 공격 결과 요약

| Stage | ATT&CK | 공격 | 결과 | 점수 |
|-------|--------|------|------|------|
| S1 | T1046 | 내부 포트 스캔 (bash /dev/tcp) | **성공** — 10개 오픈 포트 발견 | 1/1 |
| S2 | T1572 | DNS 터널링 | **실패** — secu에서 DNS(53) 서비스 미운영 | 0/1 |
| S3 | T1048.003 | ICMP 터널링 (대용량 ping) | **성공** — 20×1400B 전송 성공 | 1/1 |
| S4 | T1071.001 | HTTP C2 비콘 (Base64 쿠키) | **성공** — 15회 비콘 전송 | 1/1 |
| S5 | T1557.002 | ARP 스푸핑 | **제한적** — arping 미설치, 시뮬레이션만 | 0.5/1 |
| S6 | T1046 | nmap 상세 서비스 스캔 | **성공** — JuiceShop/Apache 식별 | 1/1 |

**Red Team 점수: 4.5 / 6**

## 상세 발견

### S1: 내부 정찰
발견된 서비스:
- secu (10.20.30.1): SSH(22)
- web (10.20.30.80): SSH(22), Apache(80), JuiceShop(3000), proxy(8082)
- siem (10.20.30.100): SSH(22), Wazuh Dashboard(443), Wazuh API(55000), agent(1514), OpenCTI(9400)

ARP 테이블: 내부망 + 외부(wifi) 모든 호스트 MAC 주소 확인됨

### S3: ICMP 터널링
- 20 패킷 × 1400바이트 = 28KB 전송 성공
- 패킷 손실 0% — IPS가 대용량 ICMP를 차단하지 않음
- **방어 필요:** Suricata에 ICMP 대용량 페이로드 탐지 룰 추가

### S4: HTTP C2 비콘
- 15회 JuiceShop 이미지 URL로 Base64 쿠키 전송
- 주기적 패턴 생성 — SIEM에서 패턴 탐지 필요
- **방어 필요:** 비정상 쿠키 패턴 + 주기적 동일 URL 접근 탐지

### S6: nmap 서비스 스캔
- JuiceShop: Node.js Express 서버 (Access-Control-Allow-Origin: *)
- HTTP 헤더에서 서버 정보 노출

## OpsClaw 위임 준수 ✅
`POST /execute-plan` 경유, SubAgent가 실행. 직접 SSH 미사용.
