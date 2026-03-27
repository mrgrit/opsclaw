# Week 09: 클라우드 보안 기초

## 학습 목표
- 클라우드 컴퓨팅의 3가지 모델(IaaS, PaaS, SaaS)을 이해한다
- IAM(Identity and Access Management)의 원칙을 설명할 수 있다
- VPC와 Security Group으로 네트워크 격리를 설계할 수 있다
- 공유 책임 모델(Shared Responsibility Model)을 이해한다

---

## 1. 클라우드 컴퓨팅 개요

### 서비스 모델

| 모델 | 사용자 관리 | 제공자 관리 | 예시 |
|------|-----------|-----------|------|
| **IaaS** | OS, 앱, 데이터 | 네트워크, 스토리지, 서버 | AWS EC2, Azure VM |
| **PaaS** | 앱, 데이터 | OS, 런타임, 인프라 | Heroku, AWS Elastic Beanstalk |
| **SaaS** | 데이터 | 전부 | Gmail, Office 365 |

### 공유 책임 모델

```
사용자 책임          |  제공자 책임
---------------------|--------------------
데이터 암호화         |  물리적 보안
접근 제어(IAM)       |  네트워크 인프라
OS 패치(IaaS)       |  하이퍼바이저
애플리케이션 보안     |  데이터센터 보안
네트워크 설정        |  하드웨어 유지보수
```

핵심: "클라우드에서의 보안"은 사용자 책임, "클라우드 자체의 보안"은 제공자 책임이다.

---

## 2. IAM (Identity and Access Management)

IAM은 "누가(Who) 무엇을(What) 어떤 조건에서(When) 할 수 있는가"를 제어한다.

### 2.1 핵심 개념

| 개념 | 설명 | 예시 |
|------|------|------|
| **User** | 개별 사용자 계정 | admin@company.com |
| **Group** | 사용자 묶음 | developers, admins |
| **Role** | 임시 권한 위임 | EC2가 S3 접근 |
| **Policy** | 권한 규칙 (JSON) | S3 읽기 허용 |

### 2.2 IAM 정책 예시

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    }
  ]
}
```

### 2.3 최소 권한 원칙 (Principle of Least Privilege)

```
나쁜 예: "Action": "*", "Resource": "*"    → 모든 권한 부여
좋은 예: "Action": "s3:GetObject"          → 필요한 권한만
```

### 2.4 IAM 보안 모범 사례

1. **root 계정 사용 금지**: 일상 업무에 root 사용하지 않기
2. **MFA 필수**: 모든 사용자에게 다중 인증 적용
3. **최소 권한**: 필요한 권한만 부여
4. **정기 감사**: 사용하지 않는 계정/키 삭제
5. **역할 사용**: 장기 자격증명 대신 임시 역할

---

## 3. VPC (Virtual Private Cloud)

VPC는 클라우드 내의 격리된 가상 네트워크이다.

### 3.1 VPC 구성요소

```
VPC (10.0.0.0/16)
├── Public Subnet (10.0.1.0/24)    ← 인터넷 접근 가능
│   ├── Internet Gateway
│   ├── Web Server
│   └── NAT Gateway
├── Private Subnet (10.0.2.0/24)   ← 인터넷 직접 접근 불가
│   ├── Application Server
│   └── → NAT Gateway 통해 외부 접근
└── DB Subnet (10.0.3.0/24)        ← 완전 격리
    └── Database
```

### 3.2 서브넷 설계 원칙

| 서브넷 | 용도 | 인터넷 | 구성 |
|--------|------|--------|------|
| Public | 웹 서버, 로드밸런서 | 직접 접근 | IGW 연결 |
| Private | 앱 서버 | NAT 통해 아웃바운드만 | NAT GW 연결 |
| Isolated | DB, 내부 서비스 | 불가 | 라우팅 없음 |

---

## 4. Security Group과 NACL

### 4.1 Security Group (보안 그룹)

인스턴스 수준의 방화벽이다. **상태 기반(Stateful)** 이다.

```
# 웹 서버 Security Group
인바운드:
  - TCP 80  (HTTP)   : 0.0.0.0/0
  - TCP 443 (HTTPS)  : 0.0.0.0/0
  - TCP 22  (SSH)    : 관리자 IP만

아웃바운드:
  - 전체 허용 (기본값)
```

```
# DB Security Group
인바운드:
  - TCP 3306 (MySQL) : 앱 서버 SG만 허용
  - TCP 22   (SSH)   : 관리자 IP만

아웃바운드:
  - 전체 허용
```

### 4.2 NACL (Network ACL)

서브넷 수준의 방화벽이다. **비상태(Stateless)** 이다.

| 항목 | Security Group | NACL |
|------|---------------|------|
| 적용 범위 | 인스턴스 | 서브넷 |
| 상태 | Stateful | Stateless |
| 규칙 | 허용만 | 허용 + 거부 |
| 평가 | 모든 규칙 | 번호 순서 |
| 기본 | 모두 거부 | 모두 허용 |

---

## 5. 실습 환경 매핑

실습 환경의 네트워크를 클라우드 VPC 개념으로 매핑해보자.

### 우리 실습 환경의 네트워크

```
외부 네트워크 (192.168.208.0/24)    ← Public Subnet에 해당
├── opsclaw (192.168.208.142)       ← 관리 서버
├── secu    (192.168.208.150)       ← 방화벽/IPS
├── web     (192.168.208.151)       ← 웹 서버
└── siem    (192.168.208.152)       ← SIEM

내부 네트워크 (10.20.30.0/24)       ← Private Subnet에 해당
├── secu    (10.20.30.1)            ← 게이트웨이 역할
├── web     (10.20.30.80)           ← 내부 웹 서비스
└── siem    (10.20.30.100)          ← 내부 모니터링
```

### 실습: nftables로 Security Group 시뮬레이션

```bash
# secu 서버에서 nftables 규칙 확인
ssh student@10.20.30.1
sudo nft list ruleset

# 이것이 클라우드의 Security Group/NACL과 같은 역할
```

---

## 6. 실습: IAM 개념 체험

OpsClaw의 API 인증이 IAM의 축소판이다.

```bash
# API 키 없이 요청 → 인증 실패
curl -s http://localhost:8000/projects | head -5

# API 키 포함 요청 → 인증 성공
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects | head -5

# 이것이 IAM의 핵심 원리:
# 1. 신원 확인 (Authentication): API 키로 "누구인가" 확인
# 2. 권한 확인 (Authorization): "무엇을 할 수 있는가" 확인
```

---

## 7. 클라우드 보안 위협 Top 5

| 순위 | 위협 | 설명 |
|------|------|------|
| 1 | IAM 설정 오류 | 과도한 권한, 키 노출 |
| 2 | 데이터 유출 | S3 공개 설정, 암호화 미적용 |
| 3 | 설정 오류 | 기본 설정 그대로 사용 |
| 4 | 불충분한 로깅 | 감사 추적 미설정 |
| 5 | 내부자 위협 | 권한 남용, 키 유출 |

---

## 8. 보안 체크리스트

- [ ] root 계정에 MFA가 적용되어 있는가?
- [ ] 사용자에게 최소 권한만 부여했는가?
- [ ] VPC가 적절히 서브넷으로 분리되어 있는가?
- [ ] Security Group이 최소 포트만 허용하는가?
- [ ] 미사용 IAM 키/계정을 삭제했는가?
- [ ] CloudTrail 등 감사 로깅이 활성화되어 있는가?

---

## 핵심 정리

1. 공유 책임 모델: 클라우드 "위의" 보안은 사용자 책임이다
2. IAM은 최소 권한 원칙을 적용하고, MFA를 필수로 설정한다
3. VPC로 네트워크를 격리하고, 서브넷으로 계층을 분리한다
4. Security Group(인스턴스)과 NACL(서브넷)로 트래픽을 제어한다
5. 클라우드 보안의 핵심은 "설정 오류 방지"이다

---

## 다음 주 예고
- Week 10: 클라우드 설정 오류 - S3 노출, 과도한 IAM 권한
