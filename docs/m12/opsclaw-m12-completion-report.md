# M12 Completion Report: Real-System Operation Test

**Date:** 2026-03-21
**Milestone:** M12 — Real-System Operation Test (실운영 테스트)
**Status:** COMPLETE ✓

---

## Summary

M12는 opsclaw를 실제 내부망 시스템(secu/web/siem)에 연결하여 실운영 테스트를 수행한 마일스톤이다.
코드 개발이 아닌 **실제 운영 시도를 통해 문제점을 발굴**하는 것이 목적이었으며, 다수의 개선 포인트를 도출했다.

---

## 테스트 환경

| 시스템 | 역할 | 관리 IP | subagent |
|--------|------|---------|---------|
| opsclaw | Master / Manager | 192.168.0.107 (wifi) | — |
| secu | 방화벽 / IPS | 192.168.0.113 (enp1s0) | :8002 ✅ |
| web | 웹서버 / WAF | 192.168.0.108 (wifi) | :8002 ✅ |
| siem | SIEM | 192.168.0.109 (wifi) | :8002 ✅ |

---

## 수행된 작업

### 인프라 설정 (secu)

**완료:**
- nftables 설치 및 설정 완료
  - `enp4s0` = 10.20.30.1/24 (내부망 게이트웨이)
  - input chain: policy drop, SSH/ICMP/내부망/opsclaw 허용
  - forward chain: enp1s0 → enp4s0 신규 연결 허용
  - NAT: enp1s0:80 → 10.20.30.80:80 포트포워딩
  - postrouting masquerade
- opsclaw → secu:8002 허용 룰 추가 (수동)

**미완료 (HOLD):**
- Suricata IPS 설치 및 inline 모드 설정

### 인프라 설정 (web)

**완료:**
- enp4s0에 10.20.30.80/24 임시 할당 (재부팅 시 소멸)

**미완료 (HOLD):**
- enp4s0 NO-CARRIER (물리 링크 미감지) — 케이블 확인 필요
- Docker 설치
- OWASP JuiceShop 컨테이너
- BunkerWeb WAF

### 인프라 설정 (siem)

**완료:**
- enp4s0에 10.20.30.100/24 임시 할당 (재부팅 시 소멸)

**미완료 (HOLD):**
- enp4s0 NO-CARRIER (물리 링크 미감지) — 케이블 확인 필요
- Wazuh manager 설치
- Wazuh agent 연동 (secu, web)
- syslog 연동

---

## 인프라 작업 HOLD 사유 및 다음 단계

**HOLD 사유:** web/siem의 enp4s0 NIC이 NO-CARRIER 상태.
`carrier=0, operstate=down` — 시스템이 현장에 없어 물리 케이블 확인 불가.

**재개 시 해야 할 것:**
1. web/siem enp4s0 케이블 물리 확인 (스위치 포트 LED)
2. 링크 UP 확인 후 내부망 IP 영구 설정 (netplan)
3. secu: Suricata 설치 → inline 모드 (`nfqueue`) → rule update (Emerging Threats)
4. web: Docker → JuiceShop → BunkerWeb WAF
5. siem: Wazuh manager → Wazuh agent (secu, web) → syslog 연동
6. 전체 통신 테스트: 외부:80 → secu NAT → web:80 → BunkerWeb → JuiceShop

---

## opsclaw 실운영 테스트를 통해 발견된 문제점

M12 테스트 중 opsclaw 자체에서 7개의 문제점 발견 → M13 개발 대상으로 이관.
상세 내용: `docs/m13/opsclaw-m13-plan.md` 참조.

---

## opsclaw 동작 확인 사항

- `GET /assets` → asset 목록 조회 정상
- `GET /assets/{id}/health` → subagent health check 정상
- `POST /projects` → project 생성 정상
- `POST /projects/{id}/plan` → plan 단계 전이 정상
- `POST /projects/{id}/execute` → execute 단계 전이 정상
- `POST /runtime/invoke` → LLM(gpt-oss:120b) 호출 및 subagent 명령 실행 정상
- `POST /a2a/run_script` (직접 호출) → shell 스크립트 실행 및 결과 반환 정상
- GPU 서버(192.168.0.105) Ollama 연동 정상 확인
