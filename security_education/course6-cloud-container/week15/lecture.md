# Week 15: 기말고사 - 클라우드 보안 설계

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 설계 + 실기 복합 시험 |
| 시간 | 120분 |
| 배점 | 100점 |
| 환경 | web (10.20.30.80), siem (10.20.30.100) |
| 제출 | 설계 문서 + 보안 설정 파일 + 보고서 |

---

## 시험 범위

- Week 02~07: Docker 보안 (이미지, 런타임, 네트워크, Compose, Bench)
- Week 09~10: 클라우드 보안 기초, 설정 오류
- Week 11~12: Kubernetes 보안, 공격
- Week 13: 클라우드 모니터링
- Week 14: IaC 보안

---

## 문제 1: 클라우드 보안 아키텍처 설계 (40점)

### 시나리오

스타트업 "SecureShop"이 온라인 쇼핑몰을 클라우드에 배포하려 한다.
아래 요구사항을 만족하는 보안 아키텍처를 설계하라.

### 요구사항

- 웹 서버 (프론트엔드): 공개 접근 필요
- API 서버 (백엔드): 웹 서버에서만 접근
- 데이터베이스: API 서버에서만 접근, 외부 접근 불가
- 관리자 접속: VPN 또는 Bastion Host 통해서만
- 모든 데이터 암호화 (저장 + 전송)
- 모니터링 및 알림 시스템

### 제출 항목 (각 10점)

**1-1. 네트워크 아키텍처 다이어그램**
- VPC, 서브넷, Security Group, NACL 설계
- 트래픽 흐름 표시

**1-2. IAM 정책 설계**
- 역할별 최소 권한 정책 (개발자, 운영자, 모니터링)
- 서비스 간 역할(Role) 정의

**1-3. 보안 설정 체크리스트**
- Docker/K8s 컨테이너 보안 설정
- 데이터 암호화 방안
- 시크릿 관리 방안

**1-4. 모니터링 계획**
- 로깅 대상 및 보관 기간
- 알림 규칙 정의
- 인시던트 대응 절차

---

## 문제 2: Docker 보안 종합 실기 (35점)

### 2-1. 이미지 스캐닝 + 보고 (10점)

```bash
ssh student@10.20.30.80

# 실행 중인 모든 컨테이너의 이미지를 스캔
# CRITICAL/HIGH 취약점 요약 보고서 작성

for img in $(docker ps --format '{{.Image}}' | sort -u); do
  echo "=== $img ==="
  trivy image --severity CRITICAL,HIGH "$img" 2>/dev/null | tail -10
  echo ""
done > /tmp/final-scan-report.txt
```

### 2-2. 보안 강화 Compose 작성 (15점)

아래 서비스를 포함하는 보안 강화 docker-compose.yaml을 작성하라:

- **nginx** (리버스 프록시): 외부 접근 가능, HTTPS만
- **app** (Python API): 내부만 접근, DB 연결
- **redis** (캐시): 내부만 접근
- **postgres** (DB): 내부만 접근

필수 보안 요구사항:
- 모든 컨테이너 비root 실행
- 읽기 전용 파일시스템
- 네트워크 분리 (frontend/backend/cache)
- Secrets 사용
- 리소스 제한
- Healthcheck

### 2-3. Docker Bench 실행 및 개선 (10점)

```bash
# Docker Bench 실행
# WARN 항목 중 3개를 선택하여 개선 조치 수행
# 개선 전후 비교 보고서 작성
```

---

## 문제 3: AI 활용 보안 분석 (25점)

### 3-1. IaC 보안 검토 (10점)

아래 Terraform 코드의 보안 문제를 LLM으로 분석하라.

```hcl
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = "t3.large"
  key_name      = "my-key"

  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
    #!/bin/bash
    echo "DB_PASSWORD=prod_secret_123" >> /etc/environment
    apt-get update && apt-get install -y docker.io
    docker run -d --privileged -p 80:80 myapp:latest
  EOF
}

resource "aws_security_group" "web" {
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

```bash
# LLM으로 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "클라우드 보안 전문가입니다. IaC 코드의 보안 문제를 분석합니다."},
      {"role": "user", "content": "[위 Terraform 코드 삽입] 이 코드의 모든 보안 문제를 찾고 수정된 코드를 제시해주세요."}
    ]
  }' | python3 -m json.tool
```

### 3-2. 보안 이벤트 분석 (15점)

```bash
# Wazuh 알림을 LLM으로 분석하여 인시던트 보고서 작성
# siem 서버에서 최근 알림 수집 후 분석

# OpsClaw로 자동화
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "final-exam-monitoring",
    "request_text": "보안 이벤트 수집 및 LLM 분석",
    "master_mode": "external"
  }'

# LLM 분석 결과를 인시던트 보고서 형식으로 작성
# - 이벤트 요약
# - 위협 평가 (심각도, 영향 범위)
# - 대응 권고사항
# - 재발 방지 대책
```

---

## 채점 기준

| 문제 | 배점 | 핵심 평가 기준 |
|------|------|---------------|
| 1-1 | 10 | 네트워크 설계의 적절성, 격리 수준 |
| 1-2 | 10 | 최소 권한 원칙 준수, Role 설계 |
| 1-3 | 10 | 보안 설정의 포괄성, 실현 가능성 |
| 1-4 | 10 | 모니터링 범위, 알림 규칙 적절성 |
| 2-1 | 10 | 스캔 실행, 결과 분석 정확성 |
| 2-2 | 15 | 보안 요구사항 충족도 |
| 2-3 | 10 | Bench 실행, 개선 효과 |
| 3-1 | 10 | 취약점 식별, 수정안 적절성 |
| 3-2 | 15 | 분석 깊이, 보고서 품질 |

---

## 학기 마무리

이 과목에서 학습한 내용:

1. **Docker 보안**: 이미지, 런타임, 네트워크, Compose 보안
2. **클라우드 보안**: IAM, VPC, 설정 오류, 모니터링
3. **Kubernetes 보안**: Pod Security, RBAC, NetworkPolicy, 공격 방어
4. **IaC 보안**: Terraform 보안 스캐닝, CI/CD 통합
5. **AI 활용**: LLM을 활용한 보안 분석 자동화

컨테이너와 클라우드는 현대 IT 인프라의 핵심이다.
보안을 설계 단계부터 내장(Security by Design)하는 것이 가장 중요한 원칙이다.
