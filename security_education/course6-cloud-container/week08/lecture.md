# Week 08: 중간고사 - Docker 보안 강화

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 실기 시험 (실습 환경에서 직접 수행) |
| 시간 | 90분 |
| 배점 | 100점 |
| 환경 | web 서버 (10.20.30.80) |
| 제출 | 보안 강화 결과 + 보고서 |

---

## 시험 범위

- Week 02: Docker 기초 + 보안 (이미지, 컨테이너, Dockerfile)
- Week 03: 이미지 보안 (Trivy 스캐닝, 베이스 이미지)
- Week 04: 런타임 보안 (capability, seccomp, 컨테이너 탈출)
- Week 05: 네트워크 보안 (격리, 포트 노출)
- Week 06: Docker Compose 보안 (secrets, 리소스 제한)
- Week 07: Docker Bench, CIS Benchmark

---

## 과제: 취약한 Docker 환경 보안 강화

### 상황 설명

아래의 취약한 `docker-compose.yaml`이 프로덕션에 배포되어 있다.
보안 점검을 수행하고, 발견된 모든 문제를 수정하라.

### 취약한 Compose 파일

```yaml
# /tmp/midterm/docker-compose.yaml (취약한 버전)
version: "3.9"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - ADMIN_TOKEN=super-secret-token-12345

  api:
    image: python:3.11
    command: python app.py
    ports:
      - "5000:5000"
      - "22:22"
    privileged: true
    environment:
      - DB_PASSWORD=password123
      - API_SECRET=my-api-secret

  db:
    image: mysql:8
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=root123
    volumes:
      - /:/host-root
```

---

## 문제 1: 취약점 식별 (30점)

위 Compose 파일에서 보안 취약점을 모두 찾아 나열하라.
각 취약점에 대해 (1) 무엇이 문제인지, (2) 왜 위험한지 설명하라.

### 예상 답안 항목

| # | 취약점 | 위험도 | 설명 |
|---|--------|--------|------|
| 1 | Docker 소켓 마운트 | CRITICAL | 호스트 전체 제어 가능 |
| 2 | 환경변수 시크릿 | HIGH | inspect로 노출 |
| 3 | --privileged | CRITICAL | 모든 보안 해제 |
| 4 | SSH 포트 노출 | HIGH | 불필요한 공격 표면 |
| 5 | DB 포트 외부 노출 | HIGH | 직접 DB 접근 가능 |
| 6 | 호스트 루트 마운트 | CRITICAL | 호스트 파일시스템 전체 노출 |
| 7 | root 실행 | MEDIUM | 권한 상승 위험 |
| 8 | full 이미지 사용 | LOW | 불필요한 패키지 포함 |
| 9 | cap_drop 미설정 | MEDIUM | 불필요한 권한 보유 |
| 10 | healthcheck 없음 | LOW | 장애 감지 불가 |

---

## 문제 2: 보안 강화 (40점)

취약한 Compose 파일을 보안 모범 사례에 맞게 수정하라.

### 수정 요구사항

1. Docker 소켓 마운트 제거
2. 환경변수 시크릿을 Docker Secrets로 교체
3. --privileged 제거, cap_drop ALL + 필요 capability만 추가
4. 불필요한 포트 제거, 필요 포트는 127.0.0.1 바인딩
5. 호스트 루트 마운트 제거, 명명된 볼륨 사용
6. 네트워크 분리 (frontend/backend)
7. 리소스 제한 설정
8. healthcheck 추가
9. read_only + no-new-privileges 적용
10. slim/alpine 이미지 사용

### 제출할 파일

```bash
# 디렉토리 구조
/tmp/midterm/
  docker-compose.yaml       # 수정된 Compose 파일
  secrets/
    db_password.txt          # DB 비밀번호
    api_secret.txt           # API 시크릿
    admin_token.txt          # 관리자 토큰
  report.md                  # 보안 점검 보고서
```

---

## 문제 3: 이미지 스캔 + 보고서 (30점)

### 3-1. Trivy 스캔 (15점)

```bash
# 사용되는 이미지의 취약점 스캔
trivy image nginx:latest --severity HIGH,CRITICAL
trivy image python:3.11 --severity HIGH,CRITICAL
trivy image mysql:8 --severity HIGH,CRITICAL

# 결과를 JSON으로 저장
trivy image -f json -o /tmp/midterm/scan-nginx.json nginx:latest
trivy image -f json -o /tmp/midterm/scan-python.json python:3.11
trivy image -f json -o /tmp/midterm/scan-mysql.json mysql:8
```

### 3-2. 보고서 작성 (15점)

보고서에 포함할 내용:

```markdown
# Docker 보안 점검 보고서

## 1. 점검 개요
- 점검 일시: YYYY-MM-DD
- 점검 대상: [서비스 목록]
- 점검 도구: Docker Bench, Trivy

## 2. 발견 사항
### 2.1 Compose 설정 취약점
- [취약점 목록과 심각도]

### 2.2 이미지 취약점
- nginx: CRITICAL X건, HIGH X건
- python: CRITICAL X건, HIGH X건
- mysql: CRITICAL X건, HIGH X건

## 3. 개선 조치
- [각 취약점에 대한 수정 내용]

## 4. 개선 전후 비교
- Docker Bench 점수: 개선 전 → 개선 후
```

---

## 채점 기준

| 항목 | 배점 | 기준 |
|------|------|------|
| 취약점 식별 | 30 | 10개 항목 x 3점 |
| Compose 수정 | 40 | 10개 요구사항 x 4점 |
| Trivy 스캔 | 15 | 3개 이미지 스캔 + 결과 분석 |
| 보고서 | 15 | 형식, 분석 깊이, 개선 전후 비교 |

---

## 참고: 모범 답안 구조 (Compose)

```yaml
version: "3.9"
services:
  web:
    image: nginx:1.25-alpine
    read_only: true
    tmpfs: [/tmp, /var/cache/nginx, /var/run]
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt: ["no-new-privileges:true"]
    ports: ["127.0.0.1:80:80"]
    networks: [frontend]
    deploy:
      resources:
        limits: { cpus: "0.5", memory: 128M }
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 5s
      retries: 3

  api:
    image: python:3.11-slim
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    networks: [frontend, backend]
    secrets: [db_password, api_secret, admin_token]
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 512M }

  db:
    image: mysql:8-oracle
    cap_drop: [ALL]
    cap_add: [CHOWN, SETUID, SETGID, DAC_OVERRIDE]
    security_opt: ["no-new-privileges:true"]
    networks: [backend]
    volumes: [db-data:/var/lib/mysql]
    secrets: [db_password]
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 1G }
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  frontend:
  backend:
    internal: true

volumes:
  db-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_secret:
    file: ./secrets/api_secret.txt
  admin_token:
    file: ./secrets/admin_token.txt
```

---

## 시험 후 안내

- 다음 주부터 클라우드 보안(AWS/Azure 개념)으로 진입한다
- Docker 보안은 클라우드 보안의 기반이 된다
- 중간고사 피드백은 Week 09에 제공한다
