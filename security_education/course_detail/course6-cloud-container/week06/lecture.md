# Week 06: Docker Compose 보안 (상세 버전)

## 학습 목표
- Docker Compose를 사용하여 다중 컨테이너 환경을 구성할 수 있다
- Docker Secrets로 비밀정보를 안전하게 관리할 수 있다
- 리소스 제한과 healthcheck를 설정할 수 있다
- Compose 파일의 보안 점검 포인트를 파악한다


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

# Week 06: Docker Compose 보안

## 학습 목표
- Docker Compose를 사용하여 다중 컨테이너 환경을 구성할 수 있다
- Docker Secrets로 비밀정보를 안전하게 관리할 수 있다
- 리소스 제한과 healthcheck를 설정할 수 있다
- Compose 파일의 보안 점검 포인트를 파악한다

---

## 1. Docker Compose 기본

Docker Compose는 여러 컨테이너를 YAML 파일 하나로 정의하고 관리한다.

```yaml
# docker-compose.yaml
version: "3.9"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: mysecret  # 이렇게 하면 안 됨!
```

```bash
# 실행
docker compose up -d

# 상태 확인
docker compose ps

# 중지 및 삭제
docker compose down
```

---

## 2. Docker Secrets

환경변수로 비밀번호를 전달하면 `docker inspect`로 노출된다.
Docker Secrets는 비밀정보를 암호화하여 컨테이너에 파일로 전달한다.

### 2.1 파일 기반 Secret

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

```bash
# 시크릿 파일 생성 (권한 제한)
mkdir -p secrets
echo "MyStr0ngP@ssw0rd" > secrets/db_password.txt
chmod 600 secrets/db_password.txt
```

### 2.2 환경변수 vs Secrets 비교

| 방법 | 보안 수준 | 노출 경로 |
|------|----------|----------|
| `environment:` | 낮음 | docker inspect, /proc/*/environ |
| `.env` 파일 | 낮음 | 파일 접근, docker inspect |
| `secrets:` | 높음 | /run/secrets/ (tmpfs, 메모리) |

---

## 3. 리소스 제한

컨테이너가 호스트 리소스를 독점하지 못하도록 제한한다.
DoS 공격이나 리소스 고갈을 방지하는 핵심 설정이다.

### 3.1 메모리/CPU 제한

```yaml
services:
  app:
    image: myapp:latest
    deploy:
      resources:
        limits:
          cpus: "0.50"      # CPU 50%
          memory: 256M       # 메모리 256MB
        reservations:
          cpus: "0.25"      # 최소 보장 CPU
          memory: 128M       # 최소 보장 메모리
```

### 3.2 PID 제한 (포크 폭탄 방지)

```yaml
services:
  app:
    image: myapp:latest
    pids_limit: 100          # 프로세스 최대 100개
```

### 3.3 스토리지 제한

```yaml
services:
  app:
    image: myapp:latest
    storage_opt:
      size: "1G"             # 컨테이너 디스크 1GB 제한
```

---

## 4. Healthcheck

컨테이너가 정상 작동하는지 주기적으로 검사한다.
문제 발생 시 자동 재시작을 트리거할 수 있다.

```yaml
services:
  web:
    image: nginx:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s          # 30초마다 검사
      timeout: 10s           # 10초 내 응답 없으면 실패
      retries: 3             # 3회 연속 실패 시 unhealthy
      start_period: 10s      # 시작 후 10초 대기

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Healthcheck 상태 확인

```bash
docker compose ps
# NAME    STATUS
# web     Up 2 minutes (healthy)
# db      Up 2 minutes (healthy)

docker inspect --format='{{.State.Health.Status}}' web
```

---

## 5. Compose 보안 설정 종합

### 5.1 완전한 보안 Compose 파일

```yaml
version: "3.9"

services:
  web:
    image: nginx:1.25-alpine
    read_only: true                    # 읽기 전용 파일시스템
    tmpfs:
      - /tmp
      - /var/cache/nginx
    cap_drop:
      - ALL                            # 모든 capability 제거
    cap_add:
      - NET_BIND_SERVICE               # 필요한 것만 추가
    security_opt:
      - no-new-privileges:true         # 권한 상승 방지
    ports:
      - "127.0.0.1:8080:80"           # localhost만 노출
    networks:
      - frontend
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 128M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  api:
    image: myapp:latest
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    networks:
      - frontend
      - backend
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
      - FOWNER
    security_opt:
      - no-new-privileges:true
    networks:
      - backend                        # 백엔드 네트워크만
    volumes:
      - db-data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  frontend:
  backend:
    internal: true                     # 외부 접근 차단

volumes:
  db-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

## 6. 실습: Compose 보안 점검

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: 기존 Compose 파일 보안 점검

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

# Apache+ModSecurity Compose 파일 확인
cat /etc/apache2/sites-enabled/ (VirtualHost 설정)

# 보안 점검 항목 확인
# 1. 환경변수에 비밀정보가 있는가?
# 2. read_only가 설정되어 있는가?
# 3. cap_drop이 설정되어 있는가?
# 4. 리소스 제한이 있는가?
# 5. healthcheck가 설정되어 있는가?
```

### 실습 2: 안전한 Compose 환경 구성

```bash
mkdir -p /tmp/secure-lab/secrets && cd /tmp/secure-lab

# 시크릿 생성
echo "LabP@ssw0rd2026" > secrets/db_password.txt
chmod 600 secrets/db_password.txt

# 보안 강화 Compose 파일 작성
cat > docker-compose.yaml << 'EOF'
version: "3.9"
services:
  web:
    image: nginx:alpine
    read_only: true
    tmpfs: [/tmp, /var/cache/nginx, /var/run]
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt: ["no-new-privileges:true"]
    ports: ["127.0.0.1:9094:80"]
    deploy:
      resources:
        limits: { cpus: "0.25", memory: 64M }
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/"]
      interval: 15s
      timeout: 5s
      retries: 3
EOF

# 실행 및 확인
docker compose up -d
docker compose ps
curl http://localhost:9094

# 정리
docker compose down
```

### 실습 3: 리소스 제한 테스트

```bash
cat > /tmp/stress-compose.yaml << 'EOF'
version: "3.9"
services:
  stress:
    image: alpine
    command: ["sh", "-c", "dd if=/dev/zero of=/dev/null bs=1M"]
    deploy:
      resources:
        limits:
          cpus: "0.1"
          memory: 32M
EOF

docker compose -f /tmp/stress-compose.yaml up -d
docker stats --no-stream  # CPU가 10%로 제한됨을 확인
docker compose -f /tmp/stress-compose.yaml down
```

---

## 7. Compose 보안 체크리스트

- [ ] 비밀정보는 secrets로 관리하는가?
- [ ] read_only 파일시스템을 적용했는가?
- [ ] cap_drop ALL + 필요한 cap_add만 설정했는가?
- [ ] no-new-privileges 옵션을 적용했는가?
- [ ] CPU/메모리/PID 리소스 제한을 설정했는가?
- [ ] healthcheck로 서비스 상태를 모니터링하는가?
- [ ] 내부 서비스는 internal 네트워크에 배치했는가?
- [ ] 포트 바인딩 시 127.0.0.1을 명시했는가?

---

## 핵심 정리

1. 환경변수 대신 Docker Secrets로 비밀정보를 관리한다
2. 리소스 제한(CPU, 메모리, PID)으로 DoS 공격을 방지한다
3. Healthcheck로 서비스 장애를 자동 감지한다
4. 보안 설정(read_only, cap_drop, no-new-privileges)을 Compose에서 일괄 적용한다
5. 네트워크를 분리하여 최소 권한 원칙을 네트워크에도 적용한다

---

## 다음 주 예고
- Week 07: Docker 보안 점검 - Docker Bench for Security, CIS Benchmark


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 06: Docker Compose 보안"의 핵심 목적은 무엇인가?
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


