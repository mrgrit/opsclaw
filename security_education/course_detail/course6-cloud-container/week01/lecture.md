# Week 01: 컨테이너/클라우드 보안 개론 (상세 버전)

## 학습 목표
- 컨테이너(Docker)의 개념과 가상머신(VM)과의 차이를 이해한다
- 클라우드 서비스 모델(IaaS/PaaS/SaaS)을 구분하고 각 특성을 설명할 수 있다
- 공유 책임 모델(Shared Responsibility Model)의 의미를 이해한다
- 실습 인프라에서 Docker 컨테이너를 직접 확인하고 기본 명령어를 사용할 수 있다
- Docker 네트워킹의 기초 개념을 파악한다
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

## 용어 해설 (Docker/클라우드/K8s 보안 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **컨테이너** | Container | 앱과 의존성을 격리하여 실행하는 경량 가상화 | 이삿짐 컨테이너 (어디서든 동일하게 열 수 있음) |
| **이미지** | Image (Docker) | 컨테이너를 만들기 위한 읽기 전용 템플릿 | 붕어빵 틀 |
| **Dockerfile** | Dockerfile | 이미지를 빌드하는 레시피 파일 | 요리 레시피 |
| **레지스트리** | Registry | 이미지를 저장·배포하는 저장소 (Docker Hub 등) | 앱 스토어 |
| **레이어** | Layer (Image) | 이미지의 각 빌드 단계 (캐싱 단위) | 레고 블록 한 층 |
| **볼륨** | Volume | 컨테이너 데이터를 영구 저장하는 공간 | 외장 하드 |
| **네임스페이스** | Namespace (Linux) | 프로세스를 격리하는 커널 기능 (PID, NET, MNT 등) | 칸막이 (같은 건물, 서로 안 보임) |
| **cgroup** | Control Group | 프로세스의 CPU/메모리 사용량을 제한하는 커널 기능 | 전기/수도 사용량 제한 |
| **오케스트레이션** | Orchestration | 다수의 컨테이너를 관리·조율하는 것 (K8s) | 오케스트라 지휘 |
| **Pod** | Pod (K8s) | K8s의 최소 배포 단위 (1개 이상의 컨테이너) | 같은 방에 사는 룸메이트들 |
| **RBAC** | Role-Based Access Control | 역할 기반 접근 제어 (K8s) | 직책별 출입 권한 |
| **PSP/PSA** | Pod Security Policy/Admission | Pod의 보안 설정을 강제하는 정책 | 건물 입주 조건 |
| **NetworkPolicy** | NetworkPolicy (K8s) | Pod 간 네트워크 통신 규칙 | 부서 간 출입 통제 |
| **Trivy** | Trivy | 컨테이너 이미지 취약점 스캐너 (Aqua) | X-ray 검사기 |
| **IaC** | Infrastructure as Code | 인프라를 코드로 정의·관리 (Terraform 등) | 건축 설계도 (코드 = 설계도) |
| **IAM** | Identity and Access Management | 클라우드 사용자/권한 관리 (AWS IAM 등) | 회사 사원증 + 권한 관리 시스템 |
| **CIS 벤치마크** | CIS Benchmark | 보안 설정 모범 사례 가이드 (Center for Internet Security) | 보안 설정 모범답안 |


# 본 강의 내용

# Week 01: 컨테이너/클라우드 보안 개론

## 학습 목표
- 컨테이너(Docker)의 개념과 가상머신(VM)과의 차이를 이해한다
- 클라우드 서비스 모델(IaaS/PaaS/SaaS)을 구분하고 각 특성을 설명할 수 있다
- 공유 책임 모델(Shared Responsibility Model)의 의미를 이해한다
- 실습 인프라에서 Docker 컨테이너를 직접 확인하고 기본 명령어를 사용할 수 있다
- Docker 네트워킹의 기초 개념을 파악한다

## 전제 조건
- 리눅스 터미널 기본 사용 경험 (ls, cd, cat 수준)
- SSH 접속 방법 숙지 (Course 1 Week 01 완료 권장)
- 운영체제 기본 개념 (프로세스, 파일시스템, 네트워크)

---

## 1. 클라우드 컴퓨팅 개론 (30분)

### 1.1 클라우드 컴퓨팅이란?

클라우드 컴퓨팅(Cloud Computing)은 인터넷을 통해 서버, 스토리지, 네트워크, 소프트웨어 등의 IT 자원을 필요한 만큼 빌려 쓰는 모델이다.

**비유**: 전기를 직접 발전하지 않고, 한전에서 공급받아 사용하는 것과 같다. 필요한 만큼 쓰고, 사용한 만큼 요금을 낸다.

### 1.2 클라우드 서비스 모델

클라우드 서비스는 제공 범위에 따라 크게 3가지로 분류한다.

```
┌──────────────────────────────────────────────────┐
│                  사용자 관리 영역                    │
│                                                    │
│  On-Premise    IaaS         PaaS        SaaS      │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  │
│  │ 어플    │  │ 어플    │  │ 어플    │  │████████│  │
│  │ 데이터  │  │ 데이터  │  │ 데이터  │  │████████│  │
│  │ 런타임  │  │ 런타임  │  │████████│  │████████│  │
│  │ 미들웨어│  │ 미들웨어│  │████████│  │████████│  │
│  │ OS      │  │ OS      │  │████████│  │████████│  │
│  │ 가상화  │  │████████│  │████████│  │████████│  │
│  │ 서버    │  │████████│  │████████│  │████████│  │
│  │ 스토리지│  │████████│  │████████│  │████████│  │
│  │ 네트워크│  │████████│  │████████│  │████████│  │
│  └────────┘  └────────┘  └────────┘  └────────┘  │
│               ████ = 클라우드 업체 관리              │
└──────────────────────────────────────────────────┘
```

| 모델 | 설명 | 제공 범위 | 대표 예시 |
|------|------|----------|----------|
| **IaaS** (Infrastructure as a Service) | 가상 서버/네트워크/스토리지 제공 | 하드웨어 + 가상화 | AWS EC2, Azure VM, GCP Compute Engine |
| **PaaS** (Platform as a Service) | 런타임 + 미들웨어까지 제공 | IaaS + OS + 런타임 | Heroku, AWS Elastic Beanstalk, Google App Engine |
| **SaaS** (Software as a Service) | 소프트웨어 전체를 서비스로 제공 | 전체 스택 | Gmail, Slack, Microsoft 365, Zoom |

**쉽게 기억하기**:
- **IaaS**: "빈 방을 빌렸다. 가구(OS, 앱)는 내가 놓는다."
- **PaaS**: "가구가 갖춰진 방을 빌렸다. 내 물건(앱)만 가져온다."
- **SaaS**: "호텔이다. 그냥 들어가서 쓴다."

### 1.3 클라우드 배포 모델

| 모델 | 설명 | 보안 특성 |
|------|------|----------|
| **퍼블릭 클라우드** | AWS, Azure 등 공유 인프라 | 비용 저렴, 멀티테넌시 보안 이슈 |
| **프라이빗 클라우드** | 조직 전용 인프라 | 보안 통제 용이, 비용 높음 |
| **하이브리드 클라우드** | 퍼블릭 + 프라이빗 혼합 | 유연하나 관리 복잡 |
| **멀티 클라우드** | 여러 퍼블릭 클라우드 병행 | 벤더 종속 회피, 보안 정책 통일 어려움 |

---

## 2. 공유 책임 모델 (20분)

### 2.1 공유 책임 모델이란?

클라우드 보안에서 가장 중요한 개념이다. **클라우드 업체와 사용자가 각각 어느 영역의 보안을 책임지는지**를 명확히 구분한 모델이다.

```
┌─────────────────────────────────────────────┐
│         고객(사용자) 책임 영역                 │
│  ┌─────────────────────────────────────┐     │
│  │ 데이터 암호화 / 접근 제어             │     │
│  │ 어플리케이션 보안                     │     │
│  │ ID/Access 관리 (IAM)                 │     │
│  │ OS 패치 (IaaS의 경우)                │     │
│  │ 네트워크 방화벽 규칙 설정             │     │
│  └─────────────────────────────────────┘     │
├─────────────────────────────────────────────┤
│         클라우드 업체 책임 영역               │
│  ┌─────────────────────────────────────┐     │
│  │ 물리적 보안 (데이터센터)              │     │
│  │ 하드웨어 유지보수                     │     │
│  │ 하이퍼바이저 보안                     │     │
│  │ 네트워크 인프라                       │     │
│  │ 글로벌 인프라 가용성                  │     │
│  └─────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

### 2.2 서비스 모델별 책임 범위

| 보안 영역 | IaaS | PaaS | SaaS |
|----------|------|------|------|
| 데이터 분류/암호화 | 사용자 | 사용자 | 사용자 |
| 애플리케이션 보안 | 사용자 | 사용자 | **업체** |
| OS 패치 | 사용자 | **업체** | **업체** |
| 네트워크 제어 | 사용자 | **업체** | **업체** |
| 물리적 보안 | **업체** | **업체** | **업체** |

**핵심 포인트**: 클라우드를 사용해도 **데이터 보안은 항상 사용자 책임**이다. "클라우드에 올리면 안전하다"는 잘못된 생각이다.

### 2.3 실제 사고 사례

| 사고 | 원인 | 책임 |
|------|------|------|
| Capital One 데이터 유출 (2019) | S3 버킷 잘못된 IAM 설정 | 사용자 |
| AWS S3 퍼블릭 버킷 노출 | 접근 제어 미설정 | 사용자 |
| Azure Cosmos DB 취약점 (2021) | 클라우드 플랫폼 버그 | 업체 |

---

## 3. 컨테이너와 Docker (30분)

### 3.1 가상화의 진화

IT 인프라는 물리 서버에서 가상머신(VM)으로, 다시 컨테이너로 진화해왔다.

```
 [물리 서버 시대]       [가상머신 시대]          [컨테이너 시대]

 ┌───────────┐       ┌───────────────┐      ┌──────────────────┐
 │  App A    │       │ VM1    VM2    │      │ C1  C2  C3  C4   │
 │  App B    │       │┌────┐┌────┐  │      │┌──┐┌──┐┌──┐┌──┐ │
 │  App C    │       ││App ││App │  │      ││A ││B ││C ││D │ │
 │           │       ││OS  ││OS  │  │      │└──┘└──┘└──┘└──┘ │
 │  OS       │       │└────┘└────┘  │      │  Docker Engine    │
 │  하드웨어  │       │ Hypervisor   │      │  Host OS         │
 │           │       │ 하드웨어      │      │  하드웨어          │
 └───────────┘       └───────────────┘      └──────────────────┘
```

### 3.2 컨테이너 vs 가상머신

| 특성 | 가상머신 (VM) | 컨테이너 (Docker) |
|------|-------------|-----------------|
| **격리 수준** | 완전 격리 (별도 OS) | 프로세스 수준 격리 |
| **크기** | 수 GB (OS 포함) | 수십 MB ~ 수백 MB |
| **시작 시간** | 수 분 | 수 초 |
| **성능 오버헤드** | 높음 | 거의 없음 |
| **이미지 수** | 서버당 수십 개 | 서버당 수백~수천 개 |
| **보안 격리** | 강함 (하이퍼바이저) | 약함 (커널 공유) |
| **사용 사례** | 멀티 OS, 강한 격리 필요 | 마이크로서비스, CI/CD |

### 3.3 Docker의 핵심 개념

**Docker**는 컨테이너를 만들고 실행하는 가장 대표적인 플랫폼이다.

| 개념 | 비유 | 설명 |
|------|------|------|
| **이미지 (Image)** | 설계도 | 컨테이너를 만들기 위한 읽기 전용 템플릿 |
| **컨테이너 (Container)** | 설계도로 지은 건물 | 이미지를 실행한 인스턴스, 독립된 환경 |
| **Dockerfile** | 설계 명세서 | 이미지를 만드는 명령어 모음 파일 |
| **레지스트리 (Registry)** | 설계도 보관소 | 이미지를 저장/공유하는 곳 (Docker Hub) |
| **볼륨 (Volume)** | 외장 하드 | 컨테이너의 데이터를 영구 저장하는 공간 |

**Docker 작동 흐름**:
```
Dockerfile → (build) → Image → (run) → Container
                         ↕
                    Docker Hub
                    (push/pull)
```

### 3.4 컨테이너 보안 위협

컨테이너는 편리하지만 특유의 보안 위협이 존재한다.

| 위협 | 설명 | 예시 |
|------|------|------|
| **이미지 취약점** | 베이스 이미지에 알려진 CVE 포함 | ubuntu:18.04에 미패치 OpenSSL |
| **컨테이너 탈출** | 컨테이너에서 호스트로 탈출 | CVE-2019-5736 (runc 취약점) |
| **과도한 권한** | --privileged, root 실행 | 호스트 장치 접근 가능 |
| **시크릿 하드코딩** | 이미지에 비밀번호/API키 포함 | Dockerfile에 ENV PASSWORD=1234 |
| **네트워크 미격리** | 컨테이너 간 무제한 통신 | 침해된 컨테이너가 DB 컨테이너 공격 |
| **커널 공유** | 모든 컨테이너가 호스트 커널 사용 | 커널 취약점 시 전체 영향 |

---

## 4. Docker 네트워킹 기초 (20분)

### 4.1 Docker 네트워크 드라이버

Docker는 컨테이너 간 통신을 위해 여러 네트워크 드라이버를 제공한다.

| 드라이버 | 설명 | 사용 사례 |
|---------|------|----------|
| **bridge** | 기본 드라이버, 같은 호스트 내 컨테이너 연결 | 단일 호스트, 개발 환경 |
| **host** | 호스트 네트워크 직접 사용 | 성능이 중요한 경우 |
| **overlay** | 여러 호스트의 컨테이너를 연결 | Docker Swarm, 분산 환경 |
| **none** | 네트워크 없음 | 보안이 극도로 중요한 경우 |
| **macvlan** | 컨테이너에 MAC 주소 부여 | 레거시 시스템 연동 |

### 4.2 Bridge 네트워크 구조

```
┌─ 호스트 (web 서버) ──────────────────────────┐
│                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Container1│  │Container2│  │Container3│   │
│  │172.17.0.2│  │172.17.0.3│  │172.17.0.4│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │         │
│  ─────┴──────────────┴──────────────┴─────   │
│              docker0 (bridge)                 │
│              172.17.0.1                       │
│                    │                          │
│              ──────┴──────                    │
│              eth0 (호스트)                     │
│              10.20.30.80                      │
└───────────────────────────────────────────────┘
```

### 4.3 보안 관점에서의 Docker 네트워킹

- **포트 매핑**: `-p 8080:80`으로 호스트 포트를 컨테이너에 연결할 때, 외부에서 직접 접근 가능해진다
- **네트워크 격리**: 별도의 bridge 네트워크를 만들어 컨테이너 그룹을 격리해야 한다
- **내부 통신**: 같은 bridge 네트워크의 컨테이너끼리는 기본적으로 자유롭게 통신 가능하다
- **DNS**: Docker는 컨테이너 이름으로 내부 DNS를 제공한다 (사용자 정의 네트워크에서)

---

## 5. 실습: Docker 컨테이너 확인 (60분)

### 실습 환경 안내

우리 실습 인프라에서 Docker를 사용하는 서버는 다음과 같다:
- **web (10.20.30.80)**: BunkerWeb WAF + JuiceShop이 Docker로 실행 중
- **siem (10.20.30.100)**: OpenCTI 및 관련 서비스가 Docker Compose로 실행 중

### 실습 5.1: web 서버 Docker 확인

web 서버에 접속하여 실행 중인 컨테이너를 확인한다.

```bash
# opsclaw 서버에서 web 서버로 SSH 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80
```

접속 후 Docker 상태를 확인한다:

```bash
# Docker 서비스 상태 확인
systemctl status docker --no-pager
# 예상 출력:
# ● docker.service - Docker Application Container Engine
#    Active: active (running) since ...
```

```bash
# Docker 버전 확인
docker --version
# 예상 출력: Docker version 24.x.x (또는 유사한 버전)
```

```bash
# 실행 중인 컨테이너 목록 확인
docker ps
# 예상 출력 (예시):
# CONTAINER ID   IMAGE              COMMAND      STATUS        PORTS                   NAMES
# a1b2c3d4e5f6   bunketweb:latest   ...          Up 2 hours    0.0.0.0:80->8080/tcp    bunkerweb
# f6e5d4c3b2a1   bwapp/juiceshop    ...          Up 2 hours    0.0.0.0:3000->3000/tcp  juiceshop
```

각 컬럼의 의미를 이해하자:
- **CONTAINER ID**: 컨테이너 고유 식별자 (해시값의 앞 12자리)
- **IMAGE**: 컨테이너를 만든 이미지 이름
- **STATUS**: 실행 상태와 경과 시간
- **PORTS**: 포트 매핑 정보 (호스트포트 -> 컨테이너포트)
- **NAMES**: 컨테이너 이름

```bash
# 정지된 컨테이너 포함 전체 목록
docker ps -a
# -a 플래그는 중지된 컨테이너도 표시한다
```

```bash
# 다운로드된 Docker 이미지 목록
docker images
# 예상 출력 (예시):
# REPOSITORY       TAG       IMAGE ID       CREATED        SIZE
# bunketweb        latest    abc123def456   2 weeks ago    250MB
# juiceshop        latest    789ghi012jkl   1 month ago    500MB
```

### 실습 5.2: 컨테이너 상세 정보 확인

특정 컨테이너의 상세 정보를 확인한다:

```bash
# 실행 중인 컨테이너 이름 확인 후, 상세 정보 조회
# (컨테이너 이름은 docker ps 출력에서 확인)
docker inspect <컨테이너이름_또는_ID>
# 출력이 매우 길다. 주요 부분만 필터링하자.
```

```bash
# 컨테이너의 IP 주소 확인
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <컨테이너이름>
# 예상 출력: 172.17.0.2 (또는 유사한 내부 IP)
```

```bash
# 컨테이너의 환경 변수 확인 (보안 관점에서 중요!)
docker inspect --format='{{range .Config.Env}}{{println .}}{{end}}' <컨테이너이름>
# 주의: 비밀번호나 API키가 노출되어 있을 수 있다!
```

```bash
# 컨테이너의 포트 매핑 확인
docker port <컨테이너이름>
# 예상 출력:
# 8080/tcp -> 0.0.0.0:80
```

```bash
# 컨테이너 리소스 사용량 실시간 모니터링
docker stats --no-stream
# 예상 출력:
# CONTAINER ID   NAME        CPU %   MEM USAGE / LIMIT     MEM %
# a1b2c3d4e5f6   bunkerweb   0.50%   128MiB / 4GiB         3.13%
# (Ctrl+C 없이 --no-stream으로 1회만 출력)
```

### 실습 5.3: 컨테이너 내부 접근

컨테이너 내부에 직접 들어가본다:

```bash
# 컨테이너 내부에서 셸 실행
docker exec -it <컨테이너이름> /bin/sh
# 또는
docker exec -it <컨테이너이름> /bin/bash
```

컨테이너 내부에서 확인할 것들:

```bash
# 컨테이너 내부에서 실행
whoami
# 예상 출력: root (보안 문제! 대부분의 컨테이너가 root로 실행된다)

hostname
# 예상 출력: a1b2c3d4e5f6 (컨테이너 ID)

cat /etc/os-release
# 컨테이너의 베이스 OS 확인

ps aux
# 실행 중인 프로세스 확인 (호스트의 프로세스는 보이지 않는다)

ip addr
# 컨테이너의 네트워크 인터페이스 확인

exit
# 컨테이너에서 나오기
```

### 실습 5.4: siem 서버 Docker 확인 (OpenCTI)

siem 서버에는 OpenCTI(위협 인텔리전스 플랫폼)가 Docker Compose로 실행 중이다.

```bash
# opsclaw 서버에서 siem 서버로 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100
```

```bash
# 실행 중인 컨테이너 확인
docker ps
# 예상 출력: OpenCTI 관련 여러 컨테이너가 보인다
# - opencti (메인 앱)
# - elasticsearch 또는 opensearch (검색엔진)
# - rabbitmq (메시지 큐)
# - redis (캐시)
# - connector-* (커넥터들)
```

```bash
# Docker Compose로 관리되는 서비스 확인
docker compose ls
# 또는
docker-compose ps
# 예상 출력: OpenCTI 프로젝트의 모든 서비스 목록
```

```bash
# Docker 네트워크 목록 확인
docker network ls
# 예상 출력:
# NETWORK ID     NAME                DRIVER    SCOPE
# abc123...      bridge              bridge    local
# def456...      opencti_default     bridge    local
# ...
```

```bash
# OpenCTI 네트워크의 상세 정보 확인
docker network inspect <opencti_네트워크_이름>
# 어떤 컨테이너들이 같은 네트워크에 있는지 확인할 수 있다
```

### 실습 5.5: Docker 로그 확인

컨테이너의 로그를 확인하는 것은 보안 모니터링의 기본이다.

```bash
# web 서버에서 (다시 접속 필요 시)
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80

# 컨테이너 로그 확인 (최근 20줄)
docker logs --tail 20 <컨테이너이름>
# 웹 서버의 최근 접근 로그를 확인할 수 있다
```

```bash
# 실시간 로그 스트리밍
docker logs -f <컨테이너이름>
# Ctrl+C로 중지
# -f 플래그는 tail -f와 같은 역할 (follow)
```

```bash
# 특정 시간 이후의 로그만 확인
docker logs --since "2026-03-27T00:00:00" <컨테이너이름>
```

### 실습 5.6: Docker 보안 기본 점검

보안 관점에서 Docker 설정을 점검한다.

```bash
# Docker 데몬 설정 확인
cat /etc/docker/daemon.json 2>/dev/null || echo "기본 설정 사용 중"
```

```bash
# root로 실행되는 컨테이너 확인 (보안 위험)
docker ps -q | while read cid; do
  name=$(docker inspect --format='{{.Name}}' $cid)
  user=$(docker inspect --format='{{.Config.User}}' $cid)
  echo "$name -> User: ${user:-root(기본값)}"
done
# root로 실행되는 컨테이너는 보안 위험이 높다
```

```bash
# Privileged 모드로 실행되는 컨테이너 확인
docker ps -q | while read cid; do
  name=$(docker inspect --format='{{.Name}}' $cid)
  priv=$(docker inspect --format='{{.HostConfig.Privileged}}' $cid)
  echo "$name -> Privileged: $priv"
done
# Privileged: true인 컨테이너는 호스트와 거의 동일한 권한을 가진다
```

```bash
# Docker 디스크 사용량 확인
docker system df
# 예상 출력:
# TYPE            TOTAL   ACTIVE   SIZE     RECLAIMABLE
# Images          5       3        1.2GB    400MB (33%)
# Containers      3       3        50MB     0B (0%)
# Local Volumes   2       2        200MB    0B (0%)
```

---

## 6. 컨테이너 보안 모범 사례 (20분)

### 6.1 보안 체크리스트

| 항목 | 안전 | 위험 |
|------|------|------|
| 실행 사용자 | `USER appuser` (비root) | `root` (기본값) |
| 이미지 | 공식 이미지, 최신 패치 | 출처 불명, 오래된 이미지 |
| 권한 | 최소 권한 | `--privileged` |
| 시크릿 | Docker Secrets, 환경변수 분리 | Dockerfile에 하드코딩 |
| 네트워크 | 필요한 포트만 노출 | `-p 0.0.0.0:포트` (전체 공개) |
| 리소스 | CPU/메모리 제한 설정 | 무제한 (호스트 자원 독점 가능) |
| 로깅 | 중앙 로그 수집 설정 | 로그 미확인 |

### 6.2 Dockerfile 보안 예시

```dockerfile
# 나쁜 예시 (보안 위험)
FROM ubuntu:latest
RUN apt-get update && apt-get install -y python3
COPY . /app
ENV DB_PASSWORD=mysecret123
CMD ["python3", "/app/main.py"]

# 좋은 예시 (보안 강화)
FROM python:3.11-slim AS builder
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER appuser
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
CMD ["python3", "main.py"]
```

---

## 과제

### 과제 1: Docker 인벤토리 작성 (필수)
web 서버와 siem 서버에서 실행 중인 모든 컨테이너의 정보를 표로 정리하라.

포함 항목:
- 서버 이름, 컨테이너 이름, 이미지, 상태, 포트 매핑, 실행 사용자

### 과제 2: 보안 점검 보고서 (필수)
실습 5.6에서 수행한 보안 점검 결과를 바탕으로 다음을 작성하라:
- 발견된 보안 이슈 목록 (root 실행, privileged 모드 등)
- 각 이슈의 위험도 (상/중/하)
- 개선 권고사항

### 과제 3: 클라우드 보안 사례 조사 (선택)
최근 1년간 발생한 클라우드 또는 컨테이너 보안 사고를 1건 조사하여 다음을 정리하라:
- 사고 개요
- 발생 원인 (공유 책임 모델 관점에서)
- 교훈 및 예방책

---

## 검증 체크리스트

실습 완료 후 다음 항목을 스스로 확인한다:

- [ ] IaaS, PaaS, SaaS의 차이를 설명할 수 있는가?
- [ ] 공유 책임 모델에서 데이터 보안의 책임이 누구에게 있는지 알고 있는가?
- [ ] 컨테이너와 VM의 차이를 3가지 이상 말할 수 있는가?
- [ ] `docker ps` 명령어로 실행 중인 컨테이너를 확인할 수 있는가?
- [ ] `docker inspect`로 컨테이너의 IP 주소를 확인할 수 있는가?
- [ ] `docker exec`로 컨테이너 내부에 접근할 수 있는가?
- [ ] `docker logs`로 컨테이너 로그를 확인할 수 있는가?
- [ ] `docker network ls`로 네트워크 목록을 확인할 수 있는가?
- [ ] Privileged 모드 컨테이너가 왜 위험한지 설명할 수 있는가?
- [ ] Dockerfile에서 보안 모범 사례 3가지를 말할 수 있는가?

---

## 다음 주 예고

**Week 02: Docker 이미지 보안과 취약점 스캐닝**
- Docker 이미지 레이어 구조 심화
- Trivy를 사용한 컨테이너 이미지 취약점 스캐닝
- 안전한 Dockerfile 작성 실습
- 실습 인프라의 이미지를 직접 스캔하여 취약점 보고서 작성


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 6)

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

**Q1.** 이번 주차 "Week 01: 컨테이너/클라우드 보안 개론"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **컨테이너 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 Docker의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **클라우드 보안 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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

