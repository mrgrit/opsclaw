# Week 10: 클라우드 설정 오류

## 학습 목표
- 클라우드 환경에서 흔히 발생하는 설정 오류를 파악할 수 있다
- S3 버킷 공개 노출의 위험과 방지 방법을 이해한다
- IAM 과도 권한의 위험을 인식하고 최소화 방법을 익힌다
- CSPM(Cloud Security Posture Management) 개념을 이해한다

---

## 1. 클라우드 설정 오류가 위험한 이유

클라우드 보안 사고의 **65% 이상**이 설정 오류에서 발생한다.
온프레미스와 달리 클라우드는 API 하나로 전 세계에 공개될 수 있다.

### 대표적 사고 사례

| 사고 | 원인 | 피해 |
|------|------|------|
| Capital One (2019) | WAF 설정 오류 + SSRF | 1억 명 개인정보 유출 |
| Twitch (2021) | Git 서버 설정 오류 | 소스코드 + 수익 정보 유출 |
| Microsoft (2023) | SAS 토큰 과도 권한 | 38TB 내부 데이터 노출 |

---

## 2. S3 버킷 보안

### 2.1 S3 공개 노출 문제

S3(Simple Storage Service)는 AWS의 객체 스토리지이다.
기본 설정이 "비공개"이지만, 잘못된 정책으로 전 세계에 공개될 수 있다.

### 2.2 위험한 S3 정책

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*"
  }]
}
```

`"Principal": "*"` 는 **모든 사람**에게 접근을 허용한다.

### 2.3 S3 보안 설정

```
1. 퍼블릭 액세스 차단 (Block Public Access)
   - BlockPublicAcls: true
   - IgnorePublicAcls: true
   - BlockPublicPolicy: true
   - RestrictPublicBuckets: true

2. 서버 측 암호화 (SSE)
   - SSE-S3: AWS 관리 키
   - SSE-KMS: 고객 관리 키 (권장)

3. 버전 관리 (Versioning)
   - 삭제/변경 시 이전 버전 복구 가능

4. 접근 로깅
   - S3 Server Access Logging 활성화
```

### 2.4 S3 보안 점검 명령어

```bash
# AWS CLI로 퍼블릭 버킷 확인 (개념 이해용)
aws s3api get-public-access-block --bucket my-bucket

# 버킷 정책 확인
aws s3api get-bucket-policy --bucket my-bucket

# 암호화 설정 확인
aws s3api get-bucket-encryption --bucket my-bucket
```

---

## 3. IAM 과도 권한

### 3.1 흔한 IAM 설정 오류

| 오류 | 위험 | 올바른 설정 |
|------|------|------------|
| `Action: "*"` | 모든 AWS 서비스 제어 가능 | 필요한 Action만 나열 |
| `Resource: "*"` | 모든 리소스 접근 | 특정 ARN 지정 |
| 장기 Access Key | 유출 시 영구 접근 | IAM Role + 임시 자격증명 |
| 미사용 계정 | 공격 진입점 | 90일 미사용 시 비활성화 |

### 3.2 위험한 IAM 정책 vs 안전한 정책

```json
// 위험: 관리자 전체 권한
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
  }]
}
```

```json
// 안전: 특정 S3 버킷의 읽기만 허용
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": [
      "arn:aws:s3:::logs-bucket",
      "arn:aws:s3:::logs-bucket/*"
    ],
    "Condition": {
      "IpAddress": {
        "aws:SourceIp": "10.0.0.0/8"
      }
    }
  }]
}
```

### 3.3 IAM Access Analyzer

AWS IAM Access Analyzer는 외부에 공유된 리소스를 자동 탐지한다.

```bash
# Access Analyzer 결과 조회 (개념)
aws accessanalyzer list-findings --analyzer-arn arn:aws:...
```

---

## 4. 기타 주요 설정 오류

### 4.1 보안 그룹 과도 허용

```
# 위험: 전 세계에서 SSH 접근 가능
인바운드 규칙:
  TCP 22 → 0.0.0.0/0

# 안전: 관리자 IP만 허용
인바운드 규칙:
  TCP 22 → 10.20.30.0/24
```

### 4.2 암호화 미적용

| 대상 | 암호화 방법 |
|------|-----------|
| 저장 데이터 (at rest) | S3 SSE, EBS 암호화, RDS 암호화 |
| 전송 데이터 (in transit) | TLS/HTTPS 강제 |
| 비밀정보 | AWS Secrets Manager, Parameter Store |

### 4.3 로깅 미설정

```
필수 로깅:
- CloudTrail: API 호출 기록 (누가 무엇을 했는가)
- VPC Flow Logs: 네트워크 트래픽 기록
- S3 Access Logs: 버킷 접근 기록
- GuardDuty: 위협 탐지
```

---

## 5. CSPM (Cloud Security Posture Management)

CSPM은 클라우드 설정을 지속적으로 모니터링하고 위반을 탐지하는 도구이다.

### 주요 CSPM 도구

| 도구 | 유형 | 특징 |
|------|------|------|
| AWS Security Hub | AWS 네이티브 | CIS 벤치마크 자동 점검 |
| Prowler | 오픈소스 | AWS/Azure/GCP 지원 |
| ScoutSuite | 오픈소스 | 멀티 클라우드 감사 |
| Checkov | 오픈소스 | IaC 정적 분석 |

### Prowler 사용 예시

```bash
# Prowler 실행 (AWS 설정 점검)
pip install prowler
prowler aws --severity critical high

# 결과 예시
# FAIL: S3 bucket "data-bucket" has public access
# FAIL: IAM user "dev-user" has no MFA
# PASS: CloudTrail is enabled in all regions
```

---

## 6. 실습: 설정 오류 탐지

### 실습 1: Docker 환경에서 설정 오류 시뮬레이션

```bash
ssh student@10.20.30.80

# "S3 공개 노출"을 Docker 볼륨으로 시뮬레이션
# 민감 데이터가 있는 컨테이너를 외부에 노출

# 나쁜 예: 모든 데이터를 외부 공개
docker run -d --name exposed-data \
  -p 0.0.0.0:9095:80 \
  -v /var/log:/usr/share/nginx/html:ro \
  nginx:alpine

# 누구나 시스템 로그를 볼 수 있음!
curl http://10.20.30.80:9095/

# 좋은 예: 접근 제한
docker rm -f exposed-data
docker run -d --name safe-data \
  -p 127.0.0.1:9095:80 \
  -v /tmp/public-only:/usr/share/nginx/html:ro \
  nginx:alpine
```

### 실습 2: OpsClaw로 설정 점검 자동화

```bash
# OpsClaw 프로젝트 생성하여 설정 점검
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "cloud-config-audit",
    "request_text": "Docker 컨테이너 설정 보안 점검",
    "master_mode": "external"
  }'

# Stage 전환
# (반환된 project_id 사용)
# curl -X POST http://localhost:8000/projects/{id}/plan ...
# curl -X POST http://localhost:8000/projects/{id}/execute ...
```

### 실습 3: IAM 정책 분석 연습

```bash
# LLM을 활용하여 IAM 정책 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "당신은 클라우드 보안 전문가입니다."},
      {"role": "user", "content": "다음 IAM 정책의 보안 문제를 분석해주세요:\n{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"*\",\"Resource\":\"*\"}]}"}
    ]
  }' | python3 -m json.tool
```

---

## 7. 설정 오류 방지 전략

1. **Infrastructure as Code**: 수동 설정 대신 코드로 관리
2. **정책 가드레일**: 조직 수준에서 위험한 설정 차단
3. **자동 감사**: CSPM 도구로 지속적 모니터링
4. **교육**: 개발자/운영자 대상 클라우드 보안 교육
5. **최소 권한**: 기본 거부, 필요 시만 허용

---

## 핵심 정리

1. 클라우드 보안 사고의 대부분은 설정 오류에서 발생한다
2. S3 퍼블릭 액세스 차단을 반드시 활성화한다
3. IAM 정책은 최소 권한 + 특정 리소스 + 조건부 설정이 원칙이다
4. CloudTrail/VPC Flow Logs 등 로깅을 필수로 활성화한다
5. CSPM 도구로 설정을 지속적으로 모니터링한다

---

## 다음 주 예고
- Week 11: Kubernetes 보안 기초 - Pod Security, RBAC, NetworkPolicy
