# Week 01: APT 시뮬레이션 기초 — 킬체인 7단계와 MITRE ATT&CK

## 학습 목표
- APT(Advanced Persistent Threat)의 정의와 일반 공격과의 차이를 이해한다
- 사이버 킬체인(Cyber Kill Chain) 7단계를 설명하고 각 단계별 공격 기법을 매핑할 수 있다
- MITRE ATT&CK 프레임워크의 구조(Tactic-Technique-Procedure)를 이해한다
- ATT&CK Navigator를 활용하여 공격 시나리오를 시각화할 수 있다
- OpsClaw를 활용한 APT 시뮬레이션 프로젝트 설계 방법을 익힌다

## 선수 지식
- 공방전 기초 과정 이수
- 네트워크/시스템 보안 기본 개념
- Linux CLI 기본 조작

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 / Control Plane | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (공격 대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | APT 개론 및 킬체인 7단계 | 강의 |
| 0:40-1:10 | MITRE ATT&CK 구조 분석 | 강의 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | ATT&CK Navigator 실습 | 실습 |
| 2:00-2:40 | OpsClaw APT 시뮬레이션 설계 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | APT 사례 분석 토론 + 퀴즈 | 토론 |

---

# Part 1: APT 개론 (40분)

## 1.1 APT란 무엇인가?

APT(Advanced Persistent Threat)는 특정 조직을 대상으로 **장기간에 걸쳐** 은밀하게 수행되는 고도화된 사이버 공격이다.

| 특성 | 일반 공격 | APT |
|------|----------|-----|
| 목표 | 불특정 다수 | 특정 조직/기관 |
| 기간 | 수 분~수 시간 | 수 주~수 년 |
| 기법 | 알려진 취약점 | 제로데이 + 커스텀 도구 |
| 은닉 | 낮음 | 극도로 높음 |
| 동기 | 금전, 과시 | 국가 지원, 산업 스파이 |

## 1.2 사이버 킬체인 7단계

Lockheed Martin이 제안한 킬체인 모델은 APT 공격의 전체 생명주기를 7단계로 분류한다.

```
1. 정찰(Reconnaissance) → 대상 정보 수집
2. 무기화(Weaponization) → 공격 페이로드 제작
3. 전달(Delivery) → 피싱, 워터링홀, USB 등
4. 익스플로잇(Exploitation) → 취약점 실행
5. 설치(Installation) → 백도어/RAT 설치
6. C2(Command & Control) → 원격 제어 채널
7. 목표 달성(Actions on Objectives) → 데이터 유출, 파괴
```

> **방어자의 핵심 원칙**: 킬체인의 **어느 한 단계만 차단**하면 공격 전체가 실패한다.

## 1.3 MITRE ATT&CK 프레임워크

ATT&CK는 킬체인을 더 세분화한 **14개 전술(Tactic)**과 수백 개 기법(Technique)으로 구성된다.

| 전술 ID | 전술 | 킬체인 매핑 |
|---------|------|------------|
| TA0043 | Reconnaissance | 1단계 |
| TA0001 | Initial Access | 3-4단계 |
| TA0002 | Execution | 4단계 |
| TA0003 | Persistence | 5단계 |
| TA0004 | Privilege Escalation | 5단계 |
| TA0005 | Defense Evasion | 전 단계 |
| TA0006 | Credential Access | 6단계 |
| TA0007 | Discovery | 1단계 |
| TA0008 | Lateral Movement | 7단계 |
| TA0009 | Collection | 7단계 |
| TA0010 | Exfiltration | 7단계 |
| TA0011 | Command and Control | 6단계 |

---

# Part 2: ATT&CK Navigator 실습 (40분)

## 실습 2.1: ATT&CK Navigator로 APT 그룹 매핑

> **목적**: 실제 APT 그룹의 공격 기법을 시각화한다
> **배우는 것**: ATT&CK 기법 분류, 위협 모델링 기초

```bash
# ATT&CK Navigator 접속 (웹 기반)
# https://mitre-attack.github.io/attack-navigator/

# APT29 (Cozy Bear) 기법 목록 조회
curl -s https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for obj in data['objects']:
    if obj.get('type') == 'intrusion-set' and 'APT29' in obj.get('aliases', []):
        print(f\"Name: {obj['name']}\")
        print(f\"Description: {obj['description'][:200]}\")
"
```

## 실습 2.2: OpsClaw로 APT 시뮬레이션 프로젝트 생성

> **목적**: OpsClaw 프레임워크에서 APT 시뮬레이션 프로젝트를 설계한다
> **배우는 것**: 킬체인 단계별 태스크 설계, 위험도 분류

```bash
# APT 시뮬레이션 프로젝트 생성
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "apt-simulation-lab01",
    "request_text": "APT 킬체인 7단계 시뮬레이션: 정찰→무기화→전달→익스플로잇→설치→C2→목표달성",
    "master_mode": "external"
  }'

# 프로젝트 상태 확인
curl -H "X-API-Key: $OPSCLAW_API_KEY" http://localhost:8000/projects
```

---

# Part 3: 심화 — 실제 APT 사례 분석 (40분)

## 3.1 APT 사례: SolarWinds 공급망 공격 (2020)

킬체인 매핑:
1. **정찰**: SolarWinds 빌드 시스템 구조 파악
2. **무기화**: SUNBURST 백도어 코드 삽입
3. **전달**: 정상 소프트웨어 업데이트로 배포
4. **익스플로잇**: DLL 사이드로딩
5. **설치**: 레지스트리 기반 지속성
6. **C2**: DNS 기반 은닉 통신
7. **목표 달성**: 미국 정부기관 데이터 유출

## 3.2 토론 주제

- 킬체인의 어느 단계에서 차단이 가장 효과적이었을까?
- 공급망 공격에 대한 기존 방어 체계의 한계는?
- ATT&CK 기반 탐지 규칙으로 SUNBURST를 탐지할 수 있었을까?

---

## 검증 체크리스트
- [ ] 킬체인 7단계를 순서대로 설명할 수 있다
- [ ] ATT&CK Tactic과 Technique의 차이를 설명할 수 있다
- [ ] ATT&CK Navigator에서 특정 APT 그룹의 기법을 시각화할 수 있다
- [ ] OpsClaw에서 APT 시뮬레이션 프로젝트를 생성할 수 있다
- [ ] SolarWinds 사례를 킬체인에 매핑할 수 있다

## 자가 점검 퀴즈
1. APT의 세 가지 핵심 특성(Advanced, Persistent, Threat)을 각각 설명하시오.
2. 사이버 킬체인에서 "무기화(Weaponization)" 단계는 방어자가 직접 관찰할 수 없다. 그 이유는?
3. MITRE ATT&CK에서 T1566은 어떤 전술(Tactic)에 속하며, 어떤 공격 기법인가?
4. 킬체인 모델의 한계점 2가지를 서술하시오.
5. OpsClaw에서 APT 시뮬레이션 프로젝트를 생성할 때 `master_mode`를 `external`로 설정하는 이유는?
