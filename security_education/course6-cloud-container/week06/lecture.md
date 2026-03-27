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
ssh student@10.20.30.80

# BunkerWeb Compose 파일 확인
cat /opt/bunkerweb/docker-compose.yaml

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
