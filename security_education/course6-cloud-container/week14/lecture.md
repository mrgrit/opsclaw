# Week 14: IaC 보안

## 학습 목표
- Infrastructure as Code(IaC)의 개념과 보안 이점을 이해한다
- Terraform의 기본 문법과 보안 관련 설정을 작성할 수 있다
- IaC 보안 스캐닝 도구(Checkov, tfsec)를 사용할 수 있다
- IaC 파이프라인에 보안 검증을 통합하는 방법을 익힌다

---

## 1. Infrastructure as Code란?

IaC는 인프라를 코드로 정의하고 버전 관리하는 방법이다.

### 수동 관리 vs IaC

| 항목 | 수동 관리 | IaC |
|------|----------|-----|
| 일관성 | 사람마다 다름 | 항상 동일 |
| 감사 | 누가 변경했는지 불명확 | Git 이력 추적 |
| 재현성 | 재현 어려움 | 동일 환경 즉시 재현 |
| 속도 | 느림 | 빠름 |
| 보안 검증 | 사후 점검 | 배포 전 자동 검증 |

### 주요 IaC 도구

| 도구 | 유형 | 대상 |
|------|------|------|
| **Terraform** | 선언적 | 멀티 클라우드 |
| **CloudFormation** | 선언적 | AWS 전용 |
| **Ansible** | 명령적 | 서버 구성 |
| **Pulumi** | 프로그래밍 | 멀티 클라우드 |

---

## 2. Terraform 기본

### 2.1 HCL (HashiCorp Configuration Language)

```hcl
# main.tf - AWS EC2 인스턴스 생성
provider "aws" {
  region = "ap-northeast-2"   # 서울 리전
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}
```

### 2.2 Terraform 워크플로

```bash
terraform init      # 플러그인 다운로드
terraform plan      # 변경 사항 미리보기
terraform apply     # 실제 적용
terraform destroy   # 인프라 삭제
```

---

## 3. Terraform 보안 설정

### 3.1 안전한 Security Group

```hcl
# 나쁜 예: 전 세계에서 SSH 허용
resource "aws_security_group" "bad" {
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # 전체 허용!
  }
}

# 좋은 예: 관리자 IP만 허용
resource "aws_security_group" "good" {
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.20.30.0/24"]  # 내부 네트워크만
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "secure-sg"
  }
}
```

### 3.2 암호화된 S3 버킷

```hcl
resource "aws_s3_bucket" "secure" {
  bucket = "company-secure-data"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secure" {
  bucket = aws_s3_bucket.secure.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "secure" {
  bucket = aws_s3_bucket.secure.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "secure" {
  bucket = aws_s3_bucket.secure.id
  versioning_configuration {
    status = "Enabled"
  }
}
```

### 3.3 시크릿 관리

```hcl
# 나쁜 예: 하드코딩된 비밀번호
resource "aws_db_instance" "bad" {
  password = "MyP@ssw0rd123"   # 코드에 비밀번호!
}

# 좋은 예: 변수 + tfvars (gitignore)
variable "db_password" {
  type      = string
  sensitive = true     # plan/apply 출력에서 마스킹
}

resource "aws_db_instance" "good" {
  password = var.db_password
}

# terraform.tfvars (반드시 .gitignore에 추가)
# db_password = "MyP@ssw0rd123"
```

---

## 4. IaC 보안 스캐닝

### 4.1 Checkov

Bridgecrew(Palo Alto)의 오픈소스 IaC 스캐너이다.

```bash
# 설치
pip install checkov

# Terraform 파일 스캔
checkov -d /path/to/terraform/

# 특정 파일 스캔
checkov -f main.tf

# JSON 출력
checkov -d . -o json > checkov-result.json
```

### Checkov 결과 예시

```
Passed checks: 12, Failed checks: 5, Skipped checks: 0

Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
  FAILED for resource: aws_s3_bucket.data
  File: main.tf:15-20

Check: CKV_AWS_24: "Ensure no security groups allow ingress from 0.0.0.0/0 to port 22"
  FAILED for resource: aws_security_group.web
  File: main.tf:25-35
```

### 4.2 tfsec

Aqua Security의 Terraform 전용 스캐너이다.

```bash
# 설치
curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash

# 스캔
tfsec /path/to/terraform/

# 심각도 필터
tfsec . --minimum-severity HIGH
```

### 4.3 도구 비교

| 도구 | 지원 IaC | 특징 |
|------|---------|------|
| Checkov | Terraform, CloudFormation, K8s, Docker | 가장 포괄적 |
| tfsec | Terraform | Terraform 특화, 빠름 |
| Terrascan | Terraform, K8s, Docker | OPA 기반 정책 |
| KICS | 15+ IaC 형식 | Checkmarx 지원 |

---

## 5. CI/CD 파이프라인 통합

### 5.1 GitHub Actions에서 IaC 스캔

```yaml
# .github/workflows/iac-security.yaml
name: IaC Security Scan
on:
  pull_request:
    paths: ["terraform/**"]

jobs:
  checkov:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: terraform/
          soft_fail: false    # 실패 시 PR 차단

  tfsec:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tfsec
        uses: aquasecurity/tfsec-action@v1.0.3
        with:
          working_directory: terraform/
```

### 5.2 보안 게이트 (Security Gate)

```
코드 작성 → PR 생성 → IaC 스캔 → [통과?] → 리뷰 → 배포
                                   ↓ 실패
                              PR 차단 + 수정 요청
```

---

## 6. 실습: IaC 보안 스캐닝

### 실습 1: 취약한 Terraform 분석

```bash
# 취약한 Terraform 파일 작성
mkdir -p /tmp/iac-lab && cd /tmp/iac-lab

cat > main.tf << 'HCLEOF'
resource "aws_security_group" "web" {
  name = "web-sg"
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "company-data-2026"
}

resource "aws_db_instance" "main" {
  engine         = "mysql"
  instance_class = "db.t3.micro"
  password       = "admin123"
  publicly_accessible = true
}
HCLEOF
```

### 실습 2: LLM으로 IaC 보안 검토

```bash
TF_CODE=$(cat /tmp/iac-lab/main.tf)

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"클라우드 보안 전문가입니다. Terraform 코드의 보안 문제를 분석합니다.\"},
      {\"role\": \"user\", \"content\": \"다음 Terraform 코드의 보안 문제를 모두 찾고 수정 방법을 제시해주세요:\\n$TF_CODE\"}
    ]
  }" | python3 -m json.tool
```

### 실습 3: Docker Compose를 IaC 관점에서 분석

```bash
# Docker Compose도 IaC의 일종이다
# Checkov으로 Compose 파일 스캔 가능
pip install checkov 2>/dev/null

# web 서버의 Compose 파일 스캔
checkov -f /tmp/secure-lab/docker-compose.yaml --framework dockerfile 2>/dev/null || \
  echo "Checkov으로 Docker Compose 보안 점검 가능"
```

---

## 7. IaC 보안 체크리스트

- [ ] 코드에 하드코딩된 시크릿이 없는가?
- [ ] Security Group이 0.0.0.0/0에 민감 포트를 허용하지 않는가?
- [ ] S3 버킷에 퍼블릭 액세스 차단이 설정되어 있는가?
- [ ] 스토리지/DB에 암호화가 적용되어 있는가?
- [ ] CI/CD에 IaC 스캔이 통합되어 있는가?
- [ ] terraform.tfvars가 .gitignore에 포함되어 있는가?
- [ ] Terraform state 파일이 안전하게 저장되는가?

---

## 핵심 정리

1. IaC는 인프라를 코드로 관리하여 일관성, 감사, 보안 검증을 보장한다
2. Terraform에서 시크릿을 하드코딩하지 않고 sensitive 변수를 사용한다
3. Checkov/tfsec으로 배포 전에 보안 설정 오류를 자동 탐지한다
4. CI/CD 파이프라인에 IaC 스캔을 통합하여 보안 게이트를 구축한다
5. Docker Compose도 IaC의 일종이므로 동일한 보안 원칙을 적용한다

---

## 다음 주 예고
- Week 15: 기말고사 - 클라우드 보안 설계
