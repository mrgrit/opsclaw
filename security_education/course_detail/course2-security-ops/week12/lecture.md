# Week 12: OpenCTI (1) — 설치와 구성 (상세 버전)

## 학습 목표
- 위협 인텔리전스(CTI)의 개념과 필요성을 이해한다
- STIX/TAXII 표준을 설명할 수 있다
- OpenCTI의 구조를 이해하고 기본 설정을 수행할 수 있다
- 데이터 소스(Connector)를 연결할 수 있다


## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`


## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---


---

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |


---

# Week 12: OpenCTI (1) — 설치와 구성

## 학습 목표

- 위협 인텔리전스(CTI)의 개념과 필요성을 이해한다
- STIX/TAXII 표준을 설명할 수 있다
- OpenCTI의 구조를 이해하고 기본 설정을 수행할 수 있다
- 데이터 소스(Connector)를 연결할 수 있다

---

## 1. 위협 인텔리전스(CTI)란?

CTI(Cyber Threat Intelligence)는 사이버 위협에 대한 **정보를 수집, 분석, 공유**하는 활동이다.

### 1.1 CTI의 수준

| 수준 | 대상 | 예시 |
|------|------|------|
| **전략적** | 경영진 | "북한 APT가 금융권을 표적으로 하고 있다" |
| **전술적** | 보안팀 | "MITRE ATT&CK T1566 (피싱)을 주로 사용한다" |
| **운영적** | SOC 분석가 | "이 캠페인은 다음 주에 활성화될 가능성이 높다" |
| **기술적** | 보안장비 | "IP 1.2.3.4, 해시 abc123을 차단하라" |

### 1.2 왜 CTI가 필요한가?

```
사후 대응 (Reactive)          →    선제 대응 (Proactive)
"공격 당했다! 뭐지?"              "이 공격그룹이 이 방법으로 올 것이다"
"이 IP 뭐지?"                    "이 IP는 Lazarus 그룹의 C2 서버다"
"패턴 분석 → 대응"               "인텔리전스 → 예방 → 탐지 → 대응"
```

---

## 2. STIX/TAXII 표준

> **이 실습을 왜 하는가?**
> 보안 솔루션 운영 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> 보안 엔지니어가 인프라를 구축/운영할 때 이 솔루션의 설정과 관리가 핵심 업무이다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.


### 2.1 STIX (Structured Threat Information eXpression)

위협 정보를 표현하는 **표준 형식** (JSON 기반):

| STIX 객체 | 설명 | 예시 |
|-----------|------|------|
| Indicator | 탐지 지표 (IOC) | 악성 IP, 해시, 도메인 |
| Malware | 악성코드 정보 | WannaCry, Emotet |
| Threat Actor | 위협 행위자 | Lazarus Group, APT28 |
| Attack Pattern | 공격 기법 | MITRE ATT&CK T1059 |
| Campaign | 공격 캠페인 | Operation DreamJob |
| Vulnerability | 취약점 | CVE-2024-1234 |
| Relationship | 객체 간 관계 | "Lazarus uses WannaCry" |

**STIX 예시:**

```json
{
  "type": "indicator",
  "id": "indicator--1234",
  "name": "Malicious IP",
  "pattern": "[ipv4-addr:value = '1.2.3.4']",
  "valid_from": "2026-03-27T00:00:00Z",
  "labels": ["malicious-activity"]
}
```

### 2.2 TAXII (Trusted Automated eXchange of Intelligence Information)

STIX 데이터를 **교환하는 프로토콜**:

| 모델 | 설명 |
|------|------|
| Collection | 서버가 데이터를 보관, 클라이언트가 폴링 |
| Channel | 발행/구독 (pub/sub) 모델 |

---

## 3. OpenCTI 아키텍처

OpenCTI는 오픈소스 위협 인텔리전스 플랫폼이다.

```
┌────────────────────────────────────────────┐
│              OpenCTI Platform              │
│         https://10.20.30.100:9400          │
│                                            │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │ Frontend │  │ GraphQL  │  │ Workers │  │
│  │ (React)  │  │   API    │  │         │  │
│  └──────────┘  └────┬─────┘  └────┬────┘  │
│                     │              │       │
│  ┌──────────────────┴──────────────┘       │
│  │                                         │
│  ├── Elasticsearch / OpenSearch             │
│  ├── Redis                                 │
│  ├── MinIO (파일 저장)                      │
│  └── RabbitMQ (메시지 큐)                   │
│                                            │
│  ┌─────────── Connectors ─────────────┐    │
│  │ AlienVault OTX  │  MITRE ATT&CK   │    │
│  │ CVE             │  AbuseIPDB      │    │
│  │ VirusTotal      │  Custom Feed    │    │
│  └────────────────────────────────────┘    │
└────────────────────────────────────────────┘
```

---

## 4. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100
```

### 4.1 OpenCTI 상태 확인

```bash
echo 1 | sudo -S docker ps | grep opencti
```

**예상 출력:**
```
... opencti/platform:6.x    ... Up ...  0.0.0.0:9400->8080/tcp  opencti-platform
... opencti/worker:6.x      ... Up ...                          opencti-worker
... redis:7                 ... Up ...  6379/tcp                 opencti-redis
... rabbitmq:3              ... Up ...  5672/tcp                 opencti-rabbitmq
... minio/minio             ... Up ...  9000/tcp                 opencti-minio
... opensearchproject/...    ... Up ...  9200/tcp                 opencti-opensearch
```

### 4.2 서비스 접근 확인

```bash
# 플랫폼 헬스체크
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:9400/health
```

**예상 출력:**
```
HTTP 200
```

---

## 5. OpenCTI 웹 인터페이스

### 5.1 접속

브라우저에서:
```
http://10.20.30.100:9400
```

- 기본 계정: `admin@opencti.io` / 설치 시 설정한 비밀번호

### 5.2 주요 메뉴

| 메뉴 | 설명 |
|------|------|
| Dashboard | 전체 현황 대시보드 |
| Analysis | 보고서, 노트 |
| Events | 인시던트, 관찰 사항 |
| Observations | IOC (Indicators, Artifacts) |
| Threats | 위협 행위자, 캠페인, 악성코드 |
| Arsenal | 공격 도구, 취약점 |
| Techniques | MITRE ATT&CK 매핑 |
| Entities | 조직, 국가, 산업 |
| Data | Connectors, 데이터 관리 |

---

## 6. OpenCTI API

### 6.1 GraphQL API

OpenCTI는 GraphQL API를 사용한다:

```bash
# API 토큰은 대시보드 > Profile > API Access에서 확인
# 예시 토큰 (실제 값으로 교체)
OPENCTI_TOKEN="your-api-token-here"

# 플랫폼 정보 조회
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{"query":"{ about { version } }"}' | python3 -m json.tool
```

**예상 출력:**
```json
{
    "data": {
        "about": {
            "version": "6.x.x"
        }
    }
}
```

### 6.2 IOC(Indicator) 조회

```bash
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{
    "query": "{ indicators(first: 5) { edges { node { name pattern valid_from } } } }"
  }' | python3 -m json.tool
```

### 6.3 위협 행위자 조회

```bash
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{
    "query": "{ threatActorsIndividuals(first: 5) { edges { node { name description } } } }"
  }' | python3 -m json.tool
```

---

## 7. Connector(커넥터) 관리

### 7.1 커넥터란?

커넥터는 외부 데이터 소스에서 위협 정보를 자동으로 수집하는 플러그인이다.

| 타입 | 설명 | 예시 |
|------|------|------|
| External Import | 외부에서 데이터 가져오기 | AlienVault OTX, MITRE ATT&CK |
| Internal Import | 파일에서 데이터 가져오기 | STIX 파일, CSV |
| Internal Enrichment | 기존 데이터 보강 | VirusTotal, AbuseIPDB |
| Stream | 실시간 데이터 내보내기 | SIEM 연동 |

### 7.2 커넥터 상태 확인

```bash
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{
    "query": "{ connectors { id name active connector_type updated_at } }"
  }' | python3 -m json.tool
```

### 7.3 MITRE ATT&CK 커넥터

가장 기본적인 커넥터. 공격 기법 데이터를 가져온다:

```bash
# docker-compose.yml에서 MITRE 커넥터 확인
echo 1 | sudo -S docker ps | grep mitre
```

### 7.4 AlienVault OTX 커넥터 설정

무료 위협 인텔리전스 피드:

```yaml
# docker-compose.yml에 추가 (예시)
connector-alienvault:
  image: opencti/connector-alienvault:6.x.x
  environment:
    - OPENCTI_URL=http://opencti-platform:8080
    - OPENCTI_TOKEN=${OPENCTI_ADMIN_TOKEN}
    - CONNECTOR_ID=connector-alienvault
    - CONNECTOR_NAME=AlienVault
    - CONNECTOR_SCOPE=alienvault
    - CONNECTOR_LOG_LEVEL=info
    - ALIENVAULT_BASE_URL=https://otx.alienvault.com
    - ALIENVAULT_API_KEY=${OTX_API_KEY}
    - ALIENVAULT_TLP=white
    - ALIENVAULT_INTERVAL=3600
```

> AlienVault OTX API 키는 https://otx.alienvault.com 에서 무료로 발급받을 수 있다.

---

## 8. 수동 데이터 입력

### 8.1 STIX 파일 가져오기

```bash
# STIX 번들 파일 생성
cat << 'STIXEOF' > /tmp/test-stix-bundle.json
{
  "type": "bundle",
  "id": "bundle--lab-test-001",
  "objects": [
    {
      "type": "indicator",
      "spec_version": "2.1",
      "id": "indicator--lab-001",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "Lab Test - Malicious IP",
      "pattern": "[ipv4-addr:value = '192.168.99.99']",
      "pattern_type": "stix",
      "valid_from": "2026-03-27T00:00:00.000Z",
      "labels": ["malicious-activity"]
    },
    {
      "type": "indicator",
      "spec_version": "2.1",
      "id": "indicator--lab-002",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "Lab Test - Malicious Domain",
      "pattern": "[domain-name:value = 'evil-lab-test.example.com']",
      "pattern_type": "stix",
      "valid_from": "2026-03-27T00:00:00.000Z",
      "labels": ["malicious-activity"]
    }
  ]
}
STIXEOF
```

### 8.2 API로 STIX 데이터 업로드

```bash
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d "{
    \"query\": \"mutation { stixBundleImport(file: \\\"$(base64 -w0 /tmp/test-stix-bundle.json)\\\") }\"
  }"
```

또는 웹 UI의 Data > Import > STIX file에서 업로드한다.

---

## 9. OpenCTI + Wazuh 연동 개념

```
OpenCTI (IOC 관리)
    ↓ IOC 목록 내보내기 (STIX/TAXII)
Wazuh Manager
    ↓ CDB List로 변환
Wazuh 룰 → IOC 매칭 → 알림
```

### 9.1 IOC 목록을 Wazuh CDB로 활용

```bash
# OpenCTI에서 악성 IP 목록 추출
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{
    "query": "{ indicators(filters: {mode: and, filters: [{key: \"pattern_type\", values: [\"stix\"]}]}, first: 100) { edges { node { name pattern } } } }"
  }' | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
for edge in data.get('data',{}).get('indicators',{}).get('edges',[]):
    pattern = edge['node'].get('pattern','')
    m = re.search(r\"value\s*=\s*'([^']+)'\", pattern)
    if m:
        print(f'{m.group(1)}:malicious')
" > /tmp/opencti_iocs.cdb

cat /tmp/opencti_iocs.cdb
```

**예상 출력:**
```
192.168.99.99:malicious
evil-lab-test.example.com:malicious
```

---

## 10. 실습 과제

### 과제 1: 환경 확인

1. OpenCTI의 모든 Docker 컨테이너가 정상 동작하는지 확인
2. 웹 인터페이스에 접속하여 로그인
3. API로 버전 정보를 조회

### 과제 2: 데이터 탐색

1. 대시보드에서 현재 등록된 IOC 수를 확인
2. MITRE ATT&CK 기법 중 Initial Access(초기 접근) 기법을 검색
3. 등록된 위협 행위자(Threat Actor)를 조회

### 과제 3: STIX 데이터 입력

1. 실습용 STIX 번들을 생성 (악성 IP 3개, 악성 도메인 2개 포함)
2. OpenCTI에 업로드
3. 대시보드에서 등록된 것을 확인

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| CTI | 사이버 위협 인텔리전스 |
| STIX | 위협 정보 표현 표준 (JSON) |
| TAXII | 위협 정보 교환 프로토콜 |
| IOC | 침해 지표 (IP, 해시, 도메인) |
| Indicator | STIX의 탐지 지표 객체 |
| Threat Actor | 위협 행위자 (APT 그룹) |
| Connector | 외부 데이터 자동 수집 플러그인 |
| GraphQL | OpenCTI API 형식 |

---

## 다음 주 예고

Week 13에서는 OpenCTI를 활용한 위협 인텔리전스 분석을 다룬다:
- IOC 관리와 활용
- 공격 그룹 분석
- 위협 헌팅


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 12: OpenCTI (1) — 설치와 구성"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안 솔루션 운영의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 위협 인텔리전스(CTI)란?"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. STIX/TAXII 표준"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안 솔루션 운영 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. OpenCTI 아키텍처"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 올바른 설정의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 보안 솔루션 운영 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---
