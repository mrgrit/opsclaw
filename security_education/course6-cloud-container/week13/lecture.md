# Week 13: 클라우드 모니터링

## 학습 목표
- 클라우드 환경에서 모니터링과 로깅의 중요성을 이해한다
- CloudTrail(API 감사 로깅)의 개념과 활용 방법을 익힌다
- CloudWatch(메트릭 및 알람)의 보안 모니터링 활용을 이해한다
- 실습 환경(Wazuh)과 클라우드 모니터링을 비교 분석할 수 있다

---

## 1. 클라우드 모니터링이 필요한 이유

온프레미스와 달리 클라우드에서는:
- **API 호출 하나로** 인프라가 변경될 수 있다
- 리소스가 **수분 내에** 생성/삭제된다
- **여러 리전/서비스**에 분산된 활동을 추적해야 한다

보안 사고 시 "누가, 언제, 무엇을" 했는지 추적하려면 로깅이 필수이다.

### 모니터링 계층

| 계층 | 대상 | 도구 |
|------|------|------|
| API 활동 | 누가 어떤 API를 호출했는가 | CloudTrail |
| 리소스 상태 | CPU, 메모리, 디스크 사용량 | CloudWatch |
| 네트워크 | 트래픽 흐름, 거부된 연결 | VPC Flow Logs |
| 애플리케이션 | 에러 로그, 접근 로그 | CloudWatch Logs |
| 위협 탐지 | 이상 행위, 알려진 공격 패턴 | GuardDuty |

---

## 2. CloudTrail (API 감사 로깅)

CloudTrail은 AWS 계정의 모든 API 호출을 기록한다.
"누가, 언제, 어디서, 무엇을 했는가"를 추적한다.

### 2.1 CloudTrail 이벤트 구조

```json
{
  "eventTime": "2026-03-27T10:30:00Z",
  "eventSource": "s3.amazonaws.com",
  "eventName": "PutBucketPolicy",
  "userIdentity": {
    "type": "IAMUser",
    "userName": "dev-user",
    "arn": "arn:aws:iam::123456789:user/dev-user"
  },
  "sourceIPAddress": "203.0.113.50",
  "requestParameters": {
    "bucketName": "company-data",
    "policy": "{\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\"...}]}"
  },
  "responseElements": null,
  "errorCode": null
}
```

### 2.2 보안 이벤트 탐지

| 모니터링 대상 | CloudTrail 이벤트 |
|-------------|-------------------|
| 무단 접근 시도 | ConsoleLogin + errorCode |
| S3 정책 변경 | PutBucketPolicy, PutBucketAcl |
| IAM 변경 | CreateUser, AttachUserPolicy |
| 보안 그룹 변경 | AuthorizeSecurityGroupIngress |
| 인스턴스 생성 | RunInstances |
| 키 삭제 | DeleteAccessKey |

### 2.3 CloudTrail 쿼리 (Athena)

```sql
-- 특정 사용자의 최근 활동
SELECT eventTime, eventName, sourceIPAddress, errorCode
FROM cloudtrail_logs
WHERE userIdentity.userName = 'suspicious-user'
  AND eventTime > '2026-03-26'
ORDER BY eventTime DESC
LIMIT 50;

-- S3 공개 설정 변경 추적
SELECT eventTime, userIdentity.userName, requestParameters
FROM cloudtrail_logs
WHERE eventName IN ('PutBucketPolicy', 'PutBucketAcl')
  AND requestParameters LIKE '%Principal%*%'
ORDER BY eventTime DESC;
```

---

## 3. CloudWatch (메트릭 + 알람)

### 3.1 보안 관련 메트릭

| 메트릭 | 의미 | 임계값 예시 |
|--------|------|-----------|
| CPUUtilization | CPU 사용률 | > 90% (암호화폐 채굴 의심) |
| NetworkIn/Out | 네트워크 트래픽 | 평소 대비 10배 이상 (유출 의심) |
| StatusCheckFailed | 인스턴스 상태 | > 0 (장애) |
| UnauthorizedAccess | 무단 접근 횟수 | > 10/분 |

### 3.2 CloudWatch 알람 설정

```json
{
  "AlarmName": "High-CPU-CryptoMining",
  "MetricName": "CPUUtilization",
  "Namespace": "AWS/EC2",
  "Statistic": "Average",
  "Period": 300,
  "EvaluationPeriods": 3,
  "Threshold": 90,
  "ComparisonOperator": "GreaterThanThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:123456:security-alerts"]
}
```

### 3.3 CloudWatch Logs에서 보안 이벤트 필터링

```
# SSH 브루트포스 탐지
filter @message like /Failed password/
| stats count(*) as failures by bin(5m)
| filter failures > 10

# root 로그인 탐지
filter @message like /session opened for user root/
```

---

## 4. VPC Flow Logs

네트워크 트래픽의 메타데이터를 기록한다.

```
2 123456789012 eni-abc123 10.0.1.5 203.0.113.50 443 49152 6 25 5000 1616729292 1616729349 ACCEPT OK
2 123456789012 eni-abc123 203.0.113.100 10.0.1.5 22 12345 6 100 50000 1616729292 1616729349 REJECT OK
```

### 보안 분석 쿼리

```sql
-- 거부된 연결 Top 10 소스 IP
SELECT srcAddr, COUNT(*) as rejected
FROM vpc_flow_logs
WHERE action = 'REJECT'
GROUP BY srcAddr
ORDER BY rejected DESC
LIMIT 10;

-- 비정상 포트 스캔 탐지
SELECT srcAddr, COUNT(DISTINCT dstPort) as ports_scanned
FROM vpc_flow_logs
WHERE action = 'REJECT'
GROUP BY srcAddr
HAVING ports_scanned > 20;
```

---

## 5. 실습 환경과 클라우드 모니터링 비교

### 우리 실습 환경 vs 클라우드

| 클라우드 서비스 | 실습 환경 동등물 | 서버 |
|---------------|----------------|------|
| CloudTrail | Wazuh 에이전트 로그 | siem (10.20.30.100) |
| CloudWatch | Wazuh 대시보드 | siem (10.20.30.100) |
| VPC Flow Logs | nftables 로그 | secu (10.20.30.1) |
| GuardDuty | Suricata IPS | secu (10.20.30.1) |
| Security Hub | Wazuh SCA | siem (10.20.30.100) |

---

## 6. 실습: 모니터링 체험

### 실습 1: Wazuh에서 보안 이벤트 조회

```bash
# siem 서버의 Wazuh 알림 확인
ssh student@10.20.30.100

# 최근 알림 조회 (CloudTrail과 유사)
cat /var/ossec/logs/alerts/alerts.json | tail -5 | python3 -m json.tool
```

### 실습 2: OpsClaw로 모니터링 자동화

```bash
# OpsClaw에서 로그 수집 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "cloud-monitoring-lab",
    "request_text": "보안 이벤트 모니터링 점검",
    "master_mode": "external"
  }'
```

### 실습 3: LLM으로 로그 분석

```bash
# Wazuh 알림을 LLM으로 분석 (CloudWatch Insights 대체)
SAMPLE_LOG='{"rule":{"id":"5710","level":10,"description":"sshd: Attempt to login using a denied user."},"agent":{"name":"web"},"srcip":"192.168.1.100"}'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"보안 분석가로서 SIEM 알림을 분석해주세요.\"},
      {\"role\": \"user\", \"content\": \"다음 Wazuh 알림을 분석하고 대응 방안을 제시해주세요:\\n$SAMPLE_LOG\"}
    ]
  }" | python3 -m json.tool
```

---

## 7. 모니터링 설계 원칙

1. **모든 API 활동 기록**: CloudTrail을 모든 리전에서 활성화
2. **로그 변조 방지**: S3 버킷 잠금 + 무결성 검증
3. **실시간 알람**: 중요 이벤트에 즉각 알림
4. **장기 보존**: 규정에 따른 로그 보관 (최소 1년)
5. **중앙 집중**: 모든 로그를 단일 지점에서 분석

---

## 핵심 정리

1. CloudTrail은 "누가 무엇을 했는가"를 기록하는 API 감사 로그이다
2. CloudWatch는 메트릭 기반 모니터링과 알람을 제공한다
3. VPC Flow Logs는 네트워크 트래픽 메타데이터를 기록한다
4. 보안 모니터링은 탐지 → 알림 → 조사 → 대응 사이클로 운영한다
5. 실습 환경의 Wazuh/nftables가 클라우드 모니터링 서비스의 축소판이다

---

## 다음 주 예고
- Week 14: IaC 보안 - Terraform 보안 스캐닝
