# 6. Purple Team 결과 (Purple Team Results)

본 장에서는 4회전의 공격→방어 반복 사이클에서 LLM 에이전트가 취약점을 발견하고 방어 체계를 점진적으로 강화한 과정과 결과를 제시한다.

## 6.1 Purple Team 실행 개요

| 항목 | 내용 |
|------|------|
| 기간 | 2026-03-25, 01:45 ~ 17:45 KST (16시간) |
| 회전 수 | 4회전 (T1~T4) |
| 실행 방식 | LLM 에이전트 자율 실행 (OpsClaw API 경유) |
| 최종 판정 | **Blue Team 방어 성공** (T4에서 모든 공격 경로 차단) |

## 6.2 회전별 결과

### T1: 웹 애플리케이션 공방

| 단계 | 팀 | 결과 |
|------|-----|------|
| Red | Attack | 3건 Critical 취약점 발견 (16분 소요) |
| Purple | Advisory | 보안 권고 P1~P3 생성 |
| Blue | Defense | nftables 룰 + FTP 접근 차단 + 패스워드 변경 |

**Red 발견.** (C-01) JuiceShop 관리자 기본 패스워드 `admin123`, (C-02) FTP 디렉토리에 KeePass DB를 포함한 기밀 파일 무인증 노출, (C-03) OpsClaw Manager API 인증 부재로 원격 코드 실행(RCE) 가능.

**Blue 대응.** JuiceShop 관리자 패스워드를 `S3cur3Admin2026x`로 변경, BunkerWeb nginx에서 `/ftp/` 경로를 HTTP 403으로 차단, nftables INPUT 룰 추가.

### T2: 네트워크 경계 공방

| 단계 | 팀 | 결과 |
|------|-----|------|
| Red | Attack | opsclaw ens33 외부 인터페이스 경유 RCE 성공 |
| Purple | Advisory | ens33 차단 + uvicorn 바인딩 변경 권고 |
| Blue | Defense | opsclaw ens33 nftables 차단 완료 |

**Red 발견.** (H-01) opsclaw 서버의 ens33 외부 인터페이스가 보호되지 않아, 외부 네트워크에서 Manager API(:8000)와 SubAgent(:8002)에 직접 접근하여 임의 명령 실행이 가능.

**Blue 대응.** opsclaw 서버의 ens33 인터페이스에 대해 포트 8000, 8002의 INPUT을 nftables로 DROP 처리.

### T3: 내부 네트워크 우회 공방

| 단계 | 팀 | 결과 |
|------|-----|------|
| Red | Attack | secu masquerade IP를 이용한 FORWARD 체인 우회 |
| Purple | Advisory | secu FORWARD 체인 화이트리스트 적용 권고 |
| Blue | Defense | secu FORWARD 체인에 test2→opsclaw, test2→siem DROP 추가 |

**Red 발견.** (H-02) secu 서버의 NAT masquerade 설정으로 외부 공격자가 내부 IP(10.20.30.x)를 경유하여 opsclaw와 siem에 접근 가능. (H-03) Wazuh의 내부 포트(1514, 1515, 55000)가 내부망 전체에 노출.

**Blue 대응.** secu FORWARD 체인에 외부→opsclaw(8000, 8002) DROP, 외부→siem(1514, 1515, 55000) DROP 룰 추가. 화이트리스트 기반으로 전환.

### T4: 최종 공격 시도

| 단계 | 팀 | 결과 |
|------|-----|------|
| Red | Attack | **모든 경로 차단** — 30분 내 공격 실패 |

LLM 에이전트는 T1~T3에서 사용한 모든 공격 벡터를 재시도하였으나, 강화된 nftables 룰에 의해 전면 차단되었다. 30분간 추가적인 우회 경로를 탐색하였으나 성공하지 못하고 종료되었다.

## 6.3 발견된 취약점 종합

**표 12. Purple Team 발견 취약점**

| ID | 심각도 | 취약점 | 위치 | 발견 회전 | 조치 상태 |
|----|--------|--------|------|----------|----------|
| C-01 | Critical | JuiceShop 기본 패스워드 admin123 | web:3000 | T1 | ✅ 수정 |
| C-02 | Critical | FTP 기밀 파일 무인증 노출 | web:80/ftp/ | T1 | ✅ 차단 |
| C-03 | Critical | OpsClaw API 무인증 RCE | opsclaw:8000 | T1 | ⚠️ 네트워크 차단 |
| H-01 | High | ens33 외부 IF 미보호 | opsclaw | T2 | ✅ 차단 |
| H-02 | High | secu masquerade IP 우회 | secu | T3 | ✅ 차단 |
| H-03 | High | Wazuh 포트 내부망 노출 | siem | T3 | ✅ 차단 |
| M-01 | Medium | Maltrail UI 외부 접근 | secu:8338 | T2 | ⚠️ 미수정 |
| M-02 | Medium | PoW 리더보드 IP 노출 | opsclaw:8000 | T2 | ⚠️ 미수정 |

**심각도 분포:** Critical 3건, High 3건, Medium 2건 — 총 8건

## 6.4 방어 체계 진화 과정

```
그림 2. 회전별 방어 체계 강화

T0 (초기)    T1 (1회전 후)    T2 (2회전 후)    T3 (3회전 후)    T4 (최종)
─────────    ────────────    ────────────    ────────────    ──────────
무방비        FTP 차단         ens33 차단       FORWARD 차단     전면 방어
             PW 변경          INPUT 보강       화이트리스트화    모든 경로 차단
                                                              → Red 실패
```

**표 13. nftables 최종 방어 상태**

| 서버 | 체인 | 룰 | 효과 |
|------|------|-----|------|
| opsclaw | INPUT ens33 | 8000, 8002 DROP | 외부 API 접근 차단 |
| opsclaw | INPUT ens37 | 특정 IP→8000, 8002 DROP | 내부 비인가 접근 차단 |
| secu | FORWARD | test2→opsclaw 8000, 8002 DROP | masquerade 우회 차단 |
| secu | FORWARD | test2→siem 1514, 1515, 55000 DROP | Wazuh 포트 보호 |
| web | nginx | `/ftp/` → 403 | FTP 디렉토리 차단 |

## 6.5 탐지 현황 분석

**표 14. 공격별 탐지 현황**

| 공격 | Suricata IPS | Wazuh AuditD | BunkerWeb WAF |
|------|:---:|:---:|:---:|
| 포트 스캔 | ✓ (ET SCAN) | — | — |
| JuiceShop SQLi 로그인 | ✗ | ✗ | ✗ |
| FTP 열람 | ✗ | ✗ | ✗ |
| OpsClaw API RCE | ✗ | ⚠️ (execve) | ✗ |
| XSS | — | — | ✓ (403) |
| ICMP 터널링 | ✗ | ✗ | — |
| HTTP C2 비콘 | ✗ | ✗ | ✗ |

**탐지율 분석.** 7개 주요 공격 중 포트 스캔(Suricata)과 XSS(WAF)만 탐지되었다. **탐지율 29%(2/7)**. 핵심 공격(SQLi 로그인, FTP 열람, API RCE, ICMP 터널링, HTTP C2)은 모두 미탐지되었다. 이는 현재 탐지 체계의 근본적 한계를 보여주며, Blue Team이 생성한 커스텀 룰의 실환경 배포가 시급함을 시사한다.

## 6.6 Purple Team 핵심 발견

**(1) 방어의 점진적 강화.** 4회전의 반복 사이클을 통해 무방비 상태에서 전면 방어까지 도달하였다. 각 회전에서 LLM 에이전트는 이전 회전의 방어를 우회하는 새로운 공격 벡터를 탐색하고, Blue Team은 해당 벡터를 차단하는 방식으로 방어가 점진적으로 강화되었다.

**(2) 네트워크 차단 vs 탐지.** 최종 방어는 nftables 기반 네트워크 차단(방화벽)으로 달성되었으며, SIEM 기반 탐지·대응(Blue Team 본연의 목표)은 인프라 이슈로 완전히 실현되지 못하였다. 이는 탐지 없는 차단은 근본적 해결이 아니며, "왜 차단되었는지"를 알기 위한 탐지 체계가 병행되어야 함을 시사한다.

**(3) LLM 에이전트의 적응적 공격.** Red Team 역할의 LLM 에이전트는 이전 공격의 차단을 인지하고, 대안 경로(ens33 외부 IF, masquerade IP)를 탐색하는 적응적 행동을 보였다. 이는 사전 정의된 공격만 실행하는 CALDERA 등 기존 도구와의 차별점이다.
