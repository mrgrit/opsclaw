# Week 08: 위협 헌팅 — SIGMA 룰, ATT&CK 매핑, 프로액티브 탐지

## 학습 목표
- 위협 헌팅(Threat Hunting)의 개념과 반응형 탐지와의 차이를 이해한다
- SIGMA 룰의 구조를 이해하고 커스텀 탐지 규칙을 작성할 수 있다
- ATT&CK 기반 가설 주도형(Hypothesis-Driven) 헌팅을 수행할 수 있다
- Wazuh SIEM에서 프로액티브 탐지 쿼리를 실행할 수 있다
- OpsClaw로 자동화된 위협 헌팅 파이프라인을 구성할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 06-07 방어 및 포렌식 기법 이해
- SIEM 로그 쿼리 기본

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 헌팅 워크스테이션 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | IPS 로그 소스 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 공격 대상 / 로그 소스 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | Wazuh SIEM | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | 위협 헌팅 이론 | 강의 |
| 0:35-1:10 | SIGMA 룰 작성 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | ATT&CK 기반 가설 헌팅 | 실습 |
| 2:00-2:40 | Wazuh 프로액티브 탐지 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | 헌팅 결과 분석 토론 + 퀴즈 | 토론 |

---

# Part 1: 위협 헌팅 이론 (35분)

## 1.1 위협 헌팅이란?

위협 헌팅은 기존 보안 도구가 **탐지하지 못한 위협**을 사전에 찾아내는 프로액티브 보안 활동이다.

| 특성 | 반응형 탐지 (IDS/SIEM) | 위협 헌팅 |
|------|----------------------|----------|
| 접근 | 알림 기반 (수동) | 가설 기반 (능동) |
| 출발점 | 시그니처/룰 매칭 | TTP 가설 + 데이터 탐색 |
| 범위 | 알려진 위협 | 미지의 위협 |
| 빈도 | 실시간 | 주기적/이벤트 기반 |
| 결과 | 알림 | 새로운 탐지 규칙 |

## 1.2 위협 헌팅 프로세스

```
1. 가설 수립 → "APT 그룹 X가 우리 환경에서 T1053(Cron)을 사용했을 수 있다"
2. 데이터 수집 → 로그, 프로세스, 네트워크 데이터 수집
3. 분석 실행 → SIGMA 룰, 쿼리, 통계 분석
4. 결과 평가 → 참양성/거짓양성 분류
5. 규칙 생성 → 발견된 TTP를 자동 탐지 규칙으로 변환
```

## 1.3 헌팅 성숙도 모델 (HMM)

| 레벨 | 이름 | 설명 |
|------|------|------|
| HM0 | Initial | 자동 알림에만 의존 |
| HM1 | Minimal | IOC 검색 수행 |
| HM2 | Procedural | 문서화된 헌팅 절차 |
| HM3 | Innovative | 가설 기반 자체 헌팅 |
| HM4 | Leading | 자동화 + ML 기반 헌팅 |

---

# Part 2: SIGMA 룰 작성 실습 (35분)

## 2.1 SIGMA란?

SIGMA는 SIEM 제품에 독립적인 **표준 탐지 규칙 형식**이다. YAML로 작성하며, Splunk/Elastic/Wazuh 등으로 변환 가능하다.

## 실습 2.1: SIGMA 룰 작성

> **목적**: 커스텀 SIGMA 탐지 규칙을 작성한다
> **배우는 것**: SIGMA 문법, 조건 로직

```yaml
# sigma_cron_persistence.yml
title: Suspicious Crontab Modification
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: 비인가 crontab 수정 탐지
author: OpsClaw Training
date: 2026/04/03
references:
  - https://attack.mitre.org/techniques/T1053/003/
tags:
  - attack.persistence
  - attack.t1053.003
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall: rename
    key: crontab_mod
  condition: selection
falsepositives:
  - 정상적인 시스템 관리자의 cron 작업 변경
level: high
```

## 실습 2.2: SIGMA를 Wazuh 규칙으로 변환

> **목적**: SIGMA 룰을 Wazuh SIEM에서 사용 가능한 형태로 변환한다
> **배우는 것**: 크로스 플랫폼 탐지 규칙 관리

```bash
# sigmac를 이용한 변환
pip3 install sigma-cli
sigma convert -t wazuh -p sysmon sigma_cron_persistence.yml

# 수동 변환: Wazuh XML 규칙
cat > /tmp/custom_hunt.xml << 'EOF'
<group name="threat_hunting">
  <rule id="100301" level="10">
    <decoded_as>auditd</decoded_as>
    <field name="audit.key">crontab_mod</field>
    <description>Threat Hunt: Crontab modification detected (T1053.003)</description>
    <mitre>
      <id>T1053.003</id>
    </mitre>
  </rule>
</group>
EOF
```

---

# Part 3: ATT&CK 기반 가설 헌팅 (40분)

## 실습 3.1: 가설 주도형 헌팅

> **목적**: ATT&CK 기법을 기반으로 헌팅 가설을 수립하고 검증한다
> **배우는 것**: 체계적 헌팅 방법론

```bash
# 가설: "공격자가 T1543.002(Systemd Service)로 persistence를 설치했을 수 있다"

# 헌팅 쿼리 1: 최근 생성된 systemd 서비스
find /etc/systemd/system -name "*.service" -newer /etc/os-release \
  -exec echo "=== {} ===" \; -exec cat {} \; 2>/dev/null

# 헌팅 쿼리 2: 비정상 ExecStart 경로
grep -r "ExecStart" /etc/systemd/system/ | \
  grep -v "/usr/\|/bin/\|/sbin/" | \
  grep -v "^#"

# 헌팅 쿼리 3: 최근 enable된 서비스
journalctl -u "*.service" --since "2026-04-01" | grep "Started\|Enabled"
```

## 실습 3.2: OpsClaw 자동 헌팅 파이프라인

```bash
# 다중 서버 동시 헌팅
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"find /etc/systemd/system -name *.service -newer /etc/os-release -exec cat {} \\;","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"instruction_prompt":"crontab -l 2>/dev/null; ls -la /var/spool/cron/crontabs/","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"instruction_prompt":"grep -r \"ExecStart\" /etc/systemd/system/ | grep -v /usr/","risk_level":"low","subagent_url":"http://10.20.30.1:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'
```

---

# Part 4: Wazuh 프로액티브 탐지 (40분)

## 실습 4.1: Wazuh API로 이벤트 검색

```bash
# Wazuh API 인증
TOKEN=$(curl -s -u wazuh:wazuh -k https://10.20.30.100:55000/security/user/authenticate | jq -r .data.token)

# 최근 크리티컬 알림 조회
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.100:55000/alerts?limit=20&q=rule.level>10" | jq '.data.affected_items[].rule'

# MITRE 기법별 알림 집계
curl -s -k -H "Authorization: Bearer $TOKEN" \
  "https://10.20.30.100:55000/alerts?limit=50" | \
  jq '[.data.affected_items[].rule.mitre.id[]?] | group_by(.) | map({technique: .[0], count: length})'
```

---

## 검증 체크리스트
- [ ] SIGMA 룰을 YAML 형식으로 작성할 수 있다
- [ ] SIGMA 룰을 Wazuh XML 규칙으로 변환할 수 있다
- [ ] ATT&CK 기법 기반 헌팅 가설을 수립할 수 있다
- [ ] 다중 서버에서 동시 헌팅 쿼리를 실행할 수 있다
- [ ] 헌팅 결과를 분석하여 새로운 탐지 규칙을 생성할 수 있다

## 자가 점검 퀴즈
1. 위협 헌팅과 침입 탐지(IDS)의 근본적인 차이점을 3가지 서술하시오.
2. SIGMA 룰이 제품 독립적(vendor-agnostic)인 장점과 한계점은?
3. 가설 주도형 헌팅에서 "좋은 가설"의 조건 3가지를 제시하시오.
4. HMM Level 4(Leading)에 도달하기 위해 필요한 기술적 역량은?
5. 헌팅에서 발견한 TTP를 자동 탐지 규칙으로 변환할 때 주의할 점은?
