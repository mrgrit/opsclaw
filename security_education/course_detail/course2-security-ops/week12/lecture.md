# Week 12: OpenCTI (1) — 설치와 구성 (상세 버전)

## 학습 목표
- 위협 인텔리전스(CTI)의 개념과 필요성을 이해한다
- STIX/TAXII 표준을 설명할 수 있다
- OpenCTI의 구조를 이해하고 기본 설정을 수행할 수 있다
- 데이터 소스(Connector)를 연결할 수 있다
- 각 개념의 보안 관점에서의 위험과 대응 방안을 분석할 수 있다
- OpsClaw를 활용하여 실습 작업을 자동화하고 증적을 관리할 수 있다
- 실제 보안 사고 사례와 연결하여 학습 내용을 적용할 수 있다


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


# 본 강의 내용

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
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100
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

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 2)

이 주차에서 다루는 기술의 동작 방식을 단계별로 분해하여 이해한다.

```
[1단계] 입력/요청 → 시스템이 데이터를 수신
[2단계] 처리 → 내부 로직에 의한 데이터 처리
[3단계] 출력/응답 → 결과 반환 또는 상태 변경
[4단계] 기록 → 로그/증적 생성
```

> **왜 이 순서가 중요한가?**
> 각 단계에서 보안 검증이 누락되면 취약점이 발생한다.
> 1단계: 입력값 검증 미흡 → Injection
> 2단계: 인가 확인 누락 → Broken Access Control
> 3단계: 에러 정보 노출 → Information Disclosure
> 4단계: 로깅 실패 → Monitoring Failures

#### 개념 2: 보안 관점에서의 위험 분석

| 위험 요소 | 발생 조건 | 영향도 | 대응 방안 |
|----------|---------|--------|---------|
| 설정 미흡 | 기본 설정 사용 | 높음 | 보안 하드닝 가이드 적용 |
| 패치 누락 | 업데이트 미적용 | 높음 | 정기 패치 관리 프로세스 |
| 접근 제어 부재 | 인증/인가 미구현 | 매우 높음 | RBAC, MFA 적용 |
| 로깅 미흡 | 감사 로그 미수집 | 중간 | SIEM 연동, 로그 정책 |

#### 개념 3: 실제 사례 분석

**사례 1: 유사 취약점이 실제 피해로 이어진 경우**

실제 보안 사고에서 이 주차의 주제가 어떻게 악용되었는지 살펴본다.
공격자는 동일한 기법을 사용하여 대규모 데이터 유출, 서비스 장애, 금전적 피해를 초래하였다.

**교훈:**
- 기본적인 보안 조치의 중요성
- 탐지 체계의 필수성
- 사고 대응 절차의 사전 수립 필요성

### 도구 비교표

| 도구 | 용도 | 장점 | 단점 | 라이선스 |
|------|------|------|------|---------|
| 도구 A | 기본 점검 | 간편, 빠름 | 기능 제한 | 오픈소스 |
| 도구 B | 심층 분석 | 상세 결과 | 학습 곡선 | 상용/무료 |
| 도구 C | 자동화 | CI/CD 연동 | 오탐 가능 | 오픈소스 |


---

## 보충 실습

### 보충 실습 1: 기본 동작 확인

이론에서 배운 내용을 직접 확인하는 기초 실습이다.

```bash
# Step 1: 현재 상태 확인
echo "=== 현재 상태 ==="
# (해당 주차에 맞는 확인 명령)

# Step 2: 설정/변경 적용
echo "=== 변경 적용 ==="
# (해당 주차에 맞는 실습 명령)

# Step 3: 결과 검증
echo "=== 결과 확인 ==="
# (변경 결과 확인 명령)
```

> **트러블슈팅:**
> - 명령이 실패하면: 권한(sudo), 경로, 서비스 상태를 먼저 확인
> - 예상과 다른 결과: 이전 실습의 설정이 남아있을 수 있으므로 초기화 후 재시도
> - 타임아웃: 네트워크 연결 또는 서비스 가동 상태 확인

### 보충 실습 2: 탐지/모니터링 관점

공격자가 아닌 **방어자 관점**에서 동일한 활동을 모니터링하는 실습이다.

```bash
# siem 서버에서 관련 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5" 2>/dev/null

# Suricata 알림 확인 (해당 시)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tail -20 /var/log/suricata/fast.log" 2>/dev/null
```

> **왜 방어자 관점도 배우는가?**
> 공격 기법만 알면 "스크립트 키디"에 불과하다.
> 공격이 어떻게 탐지되는지 이해해야 진정한 보안 전문가이다.
> 이 과목의 모든 공격 실습에는 대응하는 탐지/방어 관점이 포함된다.

### 보충 실습 3: OpsClaw 자동화

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화한다.

```bash
# 프로젝트 생성 (이번 주차용)
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"weekXX-lab","request_text":"이번 주차 실습 자동화","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 실습 태스크 실행 (해당 주차에 맞게 수정)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"실습 태스크 1","instruction_prompt":"echo 실습1","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"실습 태스크 2","instruction_prompt":"echo 실습2","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }'

# Evidence 확인
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 12: OpenCTI (1) — 설치와 구성"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안 솔루션 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 방화벽/IPS의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **SIEM 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

**Q4.** OpsClaw를 통해 실습을 실행하는 가장 큰 이점은?
- (a) 속도  (b) **모든 실행의 자동 증적(evidence) 기록**  (c) 무료  (d) 간편함

**Q5.** 이 주제의 보안 위험이 높은 이유는?
- (a) 비용이 많이 들어서  (b) 복잡해서  (c) **악용 시 시스템/데이터에 직접적 피해**  (d) 법적 문제

**Q6.** 방어/대응의 핵심 원칙은?
- (a) 모든 트래픽 차단  (b) **최소 권한 + 탐지 + 대응의 조합**  (c) 서버 재시작  (d) 비밀번호 변경

**Q7.** 실습 결과를 분석할 때 가장 먼저 확인해야 하는 것은?
- (a) 서버 이름  (b) **exit_code (성공/실패 여부)**  (c) 파일 크기  (d) 날짜

**Q8.** 이 주제와 관련된 MITRE ATT&CK 전술은?
- (a) Impact만  (b) Reconnaissance만  (c) **주제에 해당하는 전술(들)**  (d) 해당 없음

**Q9.** 실무에서 이 기법/도구를 사용할 때 가장 주의할 점은?
- (a) 속도  (b) **법적 허가와 범위 준수**  (c) 비용  (d) 보고서 양식

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 관련 없음  (b) **이번 주 결과를 다음 주에서 활용/심화**  (c) 완전히 다른 주제  (d) 복습만

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:b, Q10:b

---

## 과제 (다음 주까지)

### 과제 1: 이론 정리 보고서 (30점)

이번 주차의 핵심 개념을 자신의 말로 정리하라.

| 항목 | 배점 |
|------|------|
| 핵심 개념 정의 및 설명 | 10점 |
| 실습 결과 캡처 및 해석 | 10점 |
| 보안 관점 분석 (공격↔방어) | 10점 |

### 과제 2: 실습 수행 보고서 (40점)

이번 주차의 모든 실습을 수행하고 결과를 보고서로 작성하라.

| 항목 | 배점 |
|------|------|
| 실습 명령어 및 실행 결과 캡처 | 15점 |
| 결과 해석 및 보안 의미 분석 | 15점 |
| 트러블슈팅 경험 (있는 경우) | 10점 |

### 과제 3: OpsClaw 자동화 (30점)

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화하라.

| 항목 | 배점 |
|------|------|
| 프로젝트 생성 + stage 전환 | 5점 |
| execute-plan 태스크 설계 (3개 이상) | 10점 |
| evidence/summary 결과 | 5점 |
| replay 타임라인 결과 | 5점 |
| 자동화의 이점 분석 (직접 실행 대비) | 5점 |

**제출:** 보고서(PDF 또는 MD) + OpsClaw project_id


---

## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:

- [ ] 이론 강의 내용 이해 (핵심 용어 설명 가능)
- [ ] 기본 실습 모두 수행 완료
- [ ] 보충 실습 1 (기본 동작 확인) 완료
- [ ] 보충 실습 2 (탐지/모니터링 관점) 수행
- [ ] 보충 실습 3 (OpsClaw 자동화) 수행
- [ ] 자가 점검 퀴즈 8/10 이상 정답
- [ ] 과제 1 (이론 정리) 작성
- [ ] 과제 2 (실습 보고서) 작성
- [ ] 과제 3 (OpsClaw 자동화) 완료

