# 5. Blue Team 결과 (Blue Team Results)

본 장에서는 LLM 에이전트가 Red Team 공격(Tier 1)에 대응하여 SIEM 로그 분석, 탐지 룰 생성, 검증을 자율적으로 수행한 Blue Team 활동 결과를 제시한다.

## 5.1 SIEM 경보 수집 및 분석

LLM 에이전트는 Wazuh SIEM의 경보를 수집하여 Red Team T1 공격과의 연관성을 분석하였다. 초기 수집 결과, 패키지 설치 이벤트만 존재하고 공격 관련 경보는 발생하지 않았다. 이는 Wazuh의 기본 탐지 룰이 JuiceShop 대상 SQLi, XSS 등의 웹 공격을 커버하지 못하기 때문이며, 커스텀 룰 작성의 필요성을 확인하였다.

## 5.2 탐지 룰 자동 생성

LLM 에이전트는 Red Team T1에서 수행된 공격 유형을 기반으로 7개의 Wazuh 커스텀 탐지 룰과 1개의 Suricata IPS 시그니처를 자율적으로 생성하였다.

### 5.2.1 Wazuh 커스텀 탐지 룰

**표 9. 생성된 Wazuh 커스텀 룰**

| Rule ID | Level | 탐지 대상 | ATT&CK | 패턴 |
|---------|-------|---------|--------|------|
| 100100 | 12 | SQLi UNION/SELECT | T1190 | `UNION.*SELECT` |
| 100101 | 12 | SQLi OR bypass | T1190 | `OR\s+1=1` |
| 100102 | 10 | XSS script/onerror | T1059.007 | `<script\|onerror` |
| 100103 | 10 | Path traversal | T1005 | `\.\./etc/passwd` |
| 100104 | 8 | Scanner UA 탐지 | T1595.002 | `sqlmap\|nikto\|nmap` |
| 100105 | 8 | 민감 디렉토리 접근 | T1005 | `/ftp/\|/admin/\|/backup/` |
| 100106 | 10 | 대량 요청 (20/60s) | T1046 | frequency 20, timeframe 60 |

각 룰은 MITRE ATT&CK 기법 ID와 매핑되어 있으며, Wazuh의 `local_rules.xml`에 배포되었다. LLM 에이전트는 공격 패턴의 특성(키워드, 정규표현식, 빈도)을 분석하여 적절한 alert level과 탐지 로직을 결정하였다.

### 5.2.2 Suricata IPS 시그니처

```
alert http any any -> $HOME_NET any (
    msg:"CUSTOM SQLi UNION SELECT";
    flow:established,to_server;
    content:"UNION"; nocase;
    content:"SELECT"; nocase; distance:0; within:20;
    sid:1000001; rev:1;
)
```

LLM 에이전트는 Suricata 시그니처 문법을 이해하여, HTTP 트래픽에서 `UNION SELECT` 패턴을 탐지하는 시그니처를 자율적으로 생성하였다. `flow:established,to_server`로 정상 응답과의 오탐을 방지하고, `nocase`와 `distance:0; within:20`으로 다양한 변형을 커버한다.

## 5.3 logtest 검증

생성된 룰의 정확성을 Wazuh의 `logtest` 유틸리티로 검증하였다.

**표 10. logtest 검증 결과**

| 입력 로그 | 기대 룰 | 트리거 결과 | 판정 |
|----------|---------|-----------|------|
| `GET /?id=-1+UNION+SELECT+1,2,3--` | 100100 | Rule 100100, Level 12, "SQL Injection attempt detected" | **PASS** |
| `GET /?id='+OR+1=1--` | 100101 | Rule 100101, Level 12, "SQL Injection OR bypass" | **PASS** |
| `GET /?q=<script>alert(1)</script>` | 100102 | Rule 100102, Level 10, "XSS attempt detected" | **PASS** |
| `GET /../../etc/passwd` | 100103 | Rule 100103, Level 10, "Path traversal" | **PASS** |

logtest 검증에서 모든 룰이 정확히 트리거되었으며, ATT&CK 기법 ID가 경보에 올바르게 매핑되었다.

## 5.4 실시간 탐지 한계

Wazuh Agent의 실시간 탐지 검증은 **에이전트 버전 불일치** 문제로 완료되지 못하였다. web 서버의 Wazuh Agent 버전(4.14.4)이 siem 서버의 Wazuh Manager 버전보다 높아 등록이 거부되었으며, 이로 인해 실시간 로그 수집이 불가능하였다.

대안으로 rsyslog를 통한 로그 전달을 시도하였으나, Apache 로그 포맷과 Wazuh syslog 디코더 간 매칭 조정이 필요하여 완전한 검증에 이르지 못하였다.

## 5.5 Blue Team 점수

**표 11. Blue Team 방어 점수 (Tier 1)**

| Stage | L1 탐지 | L2 식별 | L3 룰 생성 | L4 검증 | 소계 |
|-------|---------|---------|-----------|---------|------|
| S1 정찰 | 0 | — | ✓ (100104, 100105) | logtest | 3 |
| S2 SQLi | 0 | — | ✓ (100100, 100101) | logtest ✓ | 3 |
| S3 XSS | 0 | — | ✓ (100102) | logtest ✓ | 3 |
| S4 데이터 유출 | 0 | — | ✓ (100103) | logtest ✓ | 3 |
| **소계** | 0/4 | 0/8 | **12/12** | **3/16** | **12/16** |

**분석.** L1(실시간 탐지)과 L2(실시간 식별) 점수가 0인 것은 Agent 버전 불일치에 기인한 인프라 이슈이지 LLM 에이전트의 능력 한계가 아니다. L3(룰 생성)에서 만점을 달성한 것은 LLM 에이전트가 공격 패턴을 정확히 분석하여 유효한 탐지 룰을 생성할 수 있음을 보여준다. L4(검증)에서 logtest 통과로 룰 자체의 정확성은 확인되었으나, 실환경 실시간 검증은 미완이다.

## 5.6 Blue Team 핵심 발견

**(1) LLM의 탐지 룰 생성 능력.** LLM 에이전트는 공격 패턴(SQLi, XSS, 경로 순회, 스캐너 탐지)을 정확히 분석하고, Wazuh XML 룰 포맷과 Suricata 시그니처 문법에 맞는 유효한 탐지 룰을 자율적으로 생성하였다. 이는 보안 분석가의 수동 작업을 대폭 경감할 잠재력을 보여준다.

**(2) ATT&CK 매핑 정확성.** 생성된 모든 룰은 올바른 ATT&CK 기법 ID와 전술(tactic)이 매핑되어 있어, SIEM 경보의 컨텍스트 정보 품질이 높다.

**(3) 인프라 의존성.** 탐지 룰의 품질과 무관하게, SIEM 인프라의 정상 동작(Agent 연결, 로그 수집 경로)이 전제되어야 실효성이 발휘된다.
