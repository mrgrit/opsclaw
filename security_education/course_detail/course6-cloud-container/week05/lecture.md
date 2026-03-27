# Week 05: Docker 네트워크 보안 (상세 버전)

## 학습 목표
- Docker 네트워크 드라이버(bridge, host, none)를 이해한다
- 컨테이너 간 네트워크 격리를 구성할 수 있다
- 포트 노출의 보안 위험을 파악하고 최소 노출 원칙을 적용한다
- 컨테이너 간 통신을 제어하는 방법을 실습한다
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


---

# Week 05: Docker 네트워크 보안

## 학습 목표
- Docker 네트워크 드라이버(bridge, host, none)를 이해한다
- 컨테이너 간 네트워크 격리를 구성할 수 있다
- 포트 노출의 보안 위험을 파악하고 최소 노출 원칙을 적용한다
- 컨테이너 간 통신을 제어하는 방법을 실습한다

---

## 1. Docker 네트워크 기본 개념

Docker는 컨테이너에 가상 네트워크를 제공한다.
기본적으로 3가지 네트워크 드라이버를 지원한다.

### 네트워크 드라이버 비교

| 드라이버 | 격리 | 외부 접근 | 사용 시나리오 |
|---------|------|----------|-------------|
| **bridge** | O | 포트 매핑 필요 | 기본값, 대부분의 경우 |
| **host** | X | 호스트 포트 직접 사용 | 성능 필요 시 |
| **none** | 완전 | 불가 | 네트워크 불필요 서비스 |

```bash
# 네트워크 목록 확인
docker network ls

# bridge 네트워크 상세 정보
docker network inspect bridge
```

---

## 2. Bridge 네트워크와 보안

### 2.1 기본 bridge의 문제

기본 bridge(`docker0`)에 연결된 컨테이너는 **모두 서로 통신 가능**하다.

```bash
# 기본 bridge에서 실행
docker run -d --name web nginx
docker run -d --name db mysql

# web 컨테이너에서 db 컨테이너로 접근 가능!
docker exec web ping db-container-ip
```

### 2.2 사용자 정의 네트워크로 격리

```bash
# 프론트엔드/백엔드 네트워크 분리
docker network create frontend-net
docker network create backend-net

# 웹 서버는 프론트엔드에만
docker run -d --name web --network frontend-net nginx

# DB는 백엔드에만
docker run -d --name db --network backend-net mysql

# API 서버는 양쪽에 연결 (프록시 역할)
docker run -d --name api --network frontend-net node-api
docker network connect backend-net api
```

이렇게 구성하면 web에서 db로 직접 접근이 불가능하다.

### 2.3 ICC(Inter-Container Communication) 비활성화

```bash
# Docker 데몬 설정에서 ICC 비활성화
# /etc/docker/daemon.json
{
  "icc": false
}

# 데몬 재시작 필요
sudo systemctl restart docker
```

ICC를 비활성화하면 `--link`나 사용자 정의 네트워크를 통해서만 통신 가능하다.

---

## 3. 포트 노출의 보안

### 3.1 포트 매핑 주의사항

```bash
# 위험: 모든 인터페이스에 바인딩 (0.0.0.0)
docker run -d -p 3306:3306 mysql

# 안전: localhost에만 바인딩
docker run -d -p 127.0.0.1:3306:3306 mysql

# 특정 인터페이스에 바인딩
docker run -d -p 10.20.30.80:8080:80 nginx
```

### 3.2 EXPOSE vs -p 차이

```dockerfile
# Dockerfile의 EXPOSE는 문서화 목적 (실제 포트 열지 않음)
EXPOSE 8080

# docker run -p 가 실제로 포트를 열어줌
# -P (대문자): EXPOSE된 포트를 랜덤 호스트 포트에 매핑
```

### 3.3 Docker와 iptables

Docker는 자체적으로 iptables 규칙을 생성한다.
`-p`로 포트를 열면 UFW/firewalld 규칙을 **우회**할 수 있다.

```bash
# Docker가 추가한 iptables 규칙 확인
sudo iptables -L DOCKER -n

# 주의: UFW로 3306을 차단해도 docker -p 3306:3306은 열림!
# 해결: Docker 데몬 설정에서 iptables 비활성화 또는
# /etc/docker/daemon.json에 "iptables": false 추가
```

---

## 4. 네트워크 정책 패턴

### 4.1 DMZ 패턴

```
인터넷 ─── [프론트엔드 네트워크] ─── API ─── [백엔드 네트워크] ─── DB
                  │                                    │
              웹 서버                              데이터베이스
```

```bash
# DMZ 구성
docker network create --internal backend  # --internal: 외부 접근 차단
docker network create frontend

docker run -d --name db --network backend mysql
docker run -d --name api --network backend node-api
docker network connect frontend api
docker run -d --name web --network frontend -p 80:80 nginx
```

### 4.2 --internal 네트워크

```bash
# 외부 인터넷 접근이 불가능한 내부 전용 네트워크
docker network create --internal isolated-net

docker run -d --name internal-app --network isolated-net alpine sleep 3600

# 외부 접근 불가
docker exec internal-app ping -c 1 8.8.8.8
# 결과: Network is unreachable
```

---

## 5. DNS와 서비스 디스커버리 보안

사용자 정의 네트워크에서는 컨테이너 이름으로 DNS 조회가 가능하다.

```bash
docker network create app-net
docker run -d --name redis --network app-net redis
docker run -d --name app --network app-net alpine sleep 3600

# 컨테이너 이름으로 접근 가능
docker exec app ping redis
```

보안 고려사항:
- 같은 네트워크의 컨테이너 이름이 모두 노출된다
- 민감한 서비스는 별도 네트워크로 격리해야 한다

---

## 6. 실습: 네트워크 격리 구성

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: 네트워크 격리 확인

```bash
ssh web@10.20.30.80

# 현재 네트워크 구성 확인
docker network ls
docker network inspect bridge

# 실행 중인 컨테이너의 네트워크 확인
docker inspect --format='{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}' \
  bunkerweb-juiceshop-1
```

### 실습 2: 격리된 네트워크 구성

```bash
# 프론트엔드/백엔드 네트워크 생성
docker network create lab-frontend
docker network create --internal lab-backend

# 컨테이너 배치
docker run -d --name lab-web --network lab-frontend -p 9091:80 nginx
docker run -d --name lab-db --network lab-backend alpine sleep 3600
docker run -d --name lab-api --network lab-frontend alpine sleep 3600
docker network connect lab-backend lab-api

# 통신 테스트
# web → db: 불가 (다른 네트워크)
docker exec lab-web ping -c 1 lab-db 2>&1 || echo "접근 차단됨"

# api → db: 가능 (같은 backend 네트워크)
docker exec lab-api ping -c 1 lab-db

# db → 인터넷: 불가 (--internal)
docker exec lab-db ping -c 1 8.8.8.8 2>&1 || echo "외부 접근 차단됨"
```

### 실습 3: 포트 바인딩 보안

```bash
# 전체 인터페이스 노출 (위험)
docker run -d --name open-web -p 9092:80 nginx

# localhost만 노출 (안전)
docker run -d --name local-web -p 127.0.0.1:9093:80 nginx

# 확인
ss -tlnp | grep 909
# 9092는 0.0.0.0, 9093은 127.0.0.1에 바인딩됨

# 정리
docker rm -f lab-web lab-db lab-api open-web local-web
docker network rm lab-frontend lab-backend
```

---

## 7. 네트워크 보안 체크리스트

- [ ] 기본 bridge 대신 사용자 정의 네트워크를 사용하는가?
- [ ] DB 등 내부 서비스는 `--internal` 네트워크에 배치했는가?
- [ ] 포트 매핑 시 바인딩 주소를 명시했는가? (127.0.0.1)
- [ ] Docker iptables 규칙이 방화벽 정책을 우회하지 않는가?
- [ ] 불필요한 컨테이너 간 통신을 차단했는가?

---

## 핵심 정리

1. 기본 bridge 네트워크는 모든 컨테이너가 서로 통신 가능하므로 위험하다
2. 사용자 정의 네트워크로 프론트엔드/백엔드를 분리한다
3. `--internal` 플래그로 외부 인터넷 접근을 차단한다
4. `-p 127.0.0.1:port:port` 형태로 로컬 바인딩을 명시한다
5. Docker는 iptables를 우회하므로 Docker 데몬 수준에서 제어해야 한다

---

## 다음 주 예고
- Week 06: Docker Compose 보안 - secrets, 리소스 제한, healthcheck


---

---

## 심화: 컨테이너/클라우드 보안 보충

### Docker 보안 핵심 개념 상세

#### 컨테이너 격리의 원리

```
호스트 OS 커널
├── Namespace (격리)
│   ├── PID namespace  → 컨테이너마다 독립 프로세스 번호
│   ├── NET namespace  → 컨테이너마다 독립 네트워크 스택
│   ├── MNT namespace  → 컨테이너마다 독립 파일시스템
│   ├── UTS namespace  → 컨테이너마다 독립 hostname
│   └── USER namespace → 컨테이너 내 root ≠ 호스트 root (설정 시)
│
├── cgroup (자원 제한)
│   ├── CPU:    --cpus=2          → 최대 2코어
│   ├── Memory: --memory=512m     → 최대 512MB
│   └── IO:     --blkio-weight=500
│
└── Overlay FS (레이어 파일시스템)
    ├── 읽기 전용 레이어 (이미지)
    └── 읽기/쓰기 레이어 (컨테이너)
```

> **왜 컨테이너가 VM보다 가벼운가?**
> VM: 각각 전체 OS 커널을 포함 (수 GB)
> 컨테이너: 호스트 커널을 공유, 격리만 namespace로 (수 MB)
> 대신 격리 수준은 VM이 더 강하다 (커널 취약점 시 컨테이너 탈출 가능)

#### Dockerfile 보안 체크리스트

```dockerfile
# 나쁜 예
FROM ubuntu:latest          # ❌ latest 태그 (재현 불가)
RUN apt-get update && apt-get install -y curl vim  # ❌ 불필요 패키지
COPY . /app                 # ❌ 전체 복사 (.env 포함 가능)
RUN chmod 777 /app          # ❌ 과도한 권한
USER root                   # ❌ root 실행
EXPOSE 22                   # ❌ SSH 포트 (컨테이너에서 불필요)

# 좋은 예
FROM ubuntu:22.04@sha256:abc123...  # ✅ 특정 버전 + digest 고정
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*  # ✅ 최소 패키지 + 캐시 삭제
COPY --chown=appuser:appuser app/ /app  # ✅ 필요한 것만 + 소유자 지정
RUN chmod 550 /app          # ✅ 최소 권한
USER appuser                # ✅ 비root 사용자
HEALTHCHECK CMD curl -f http://localhost:8080 || exit 1  # ✅ 헬스체크
```

### 실습: Docker 보안 점검 (실습 인프라)

```bash
# web 서버의 Docker 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "
  echo '=== Docker 버전 ===' && docker --version 2>/dev/null || echo 'Docker 미설치'
  echo '=== 실행 중 컨테이너 ===' && docker ps 2>/dev/null || echo '접근 불가'
  echo '=== Docker 소켓 권한 ===' && ls -la /var/run/docker.sock 2>/dev/null
" 2>/dev/null

# siem 서버의 Docker 상태 (OpenCTI가 Docker로 실행)
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 "
  echo '=== Docker 컨테이너 ===' && sudo docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' 2>/dev/null
  echo '=== Docker 네트워크 ===' && sudo docker network ls 2>/dev/null
" 2>/dev/null
```

### CIS Docker Benchmark 핵심 항목

| # | 항목 | 점검 명령 | 기대 결과 |
|---|------|---------|---------|
| 2.1 | Docker daemon 설정 | `cat /etc/docker/daemon.json` | userns-remap 설정 |
| 4.1 | 비root 사용자 | `docker inspect --format '{{.Config.User}}' <컨테이너>` | root가 아닌 사용자 |
| 4.6 | HEALTHCHECK | `docker inspect --format '{{.Config.Healthcheck}}' <컨테이너>` | 헬스체크 설정됨 |
| 5.2 | network_mode | `docker inspect --format '{{.HostConfig.NetworkMode}}' <컨테이너>` | host가 아닌 것 |
| 5.12 | --privileged | `docker inspect --format '{{.HostConfig.Privileged}}' <컨테이너>` | false |


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 05: Docker 네트워크 보안"의 핵심 목적은 무엇인가?
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


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


