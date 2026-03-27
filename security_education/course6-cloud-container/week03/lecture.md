# Week 03: 이미지 보안

## 학습 목표
- Docker 이미지의 보안 위험을 이해한다
- Trivy를 사용하여 이미지 취약점을 스캔할 수 있다
- 안전한 베이스 이미지 선택 기준을 설명할 수 있다
- 이미지에 포함된 시크릿을 탐지할 수 있다

---

## 1. 이미지 보안이 중요한 이유

Docker 이미지는 애플리케이션과 모든 의존성을 포함한다.
이미지 내에 취약한 라이브러리, 노출된 비밀키, 불필요한 도구가 포함되면
컨테이너 실행 시 바로 공격 표면이 된다.

### 대표적인 이미지 보안 위협

| 위협 | 설명 | 예시 |
|------|------|------|
| 취약한 패키지 | 알려진 CVE가 있는 라이브러리 | Log4j, OpenSSL 취약점 |
| 시크릿 노출 | 이미지 레이어에 저장된 비밀정보 | API 키, DB 비밀번호 |
| 악성 베이스 이미지 | 신뢰할 수 없는 출처의 이미지 | Docker Hub 비공식 이미지 |
| 과도한 패키지 | 불필요한 도구 포함 | gcc, wget, curl 등 |

---

## 2. Trivy: 컨테이너 이미지 스캐너

Trivy는 Aqua Security에서 만든 오픈소스 취약점 스캐너이다.
이미지, 파일시스템, Git 저장소의 취약점을 검출한다.

### 2.1 Trivy 설치

```bash
# Ubuntu/Debian
sudo apt-get install -y wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | \
  sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update && sudo apt-get install -y trivy
```

### 2.2 이미지 스캔

```bash
# 기본 스캔: 모든 심각도 표시
trivy image nginx:latest

# HIGH, CRITICAL만 필터링
trivy image --severity HIGH,CRITICAL nginx:latest

# JSON 출력 (자동화에 활용)
trivy image -f json -o result.json nginx:latest
```

### 2.3 스캔 결과 읽기

```
nginx:latest (debian 12.4)
Total: 45 (HIGH: 12, CRITICAL: 3)

+-----------+------------------+----------+-------------------+
| Library   | Vulnerability    | Severity | Fixed Version     |
+-----------+------------------+----------+-------------------+
| libssl3   | CVE-2024-XXXXX   | CRITICAL | 3.0.13-1~deb12u1 |
| zlib1g    | CVE-2023-XXXXX   | HIGH     | 1:1.2.13.dfsg-1   |
+-----------+------------------+----------+-------------------+
```

- **CRITICAL**: 즉시 패치 필요 (원격 코드 실행 등)
- **HIGH**: 빠른 시일 내 패치 필요
- **MEDIUM/LOW**: 계획적 패치

---

## 3. 안전한 베이스 이미지 선택

### 3.1 이미지 크기와 보안의 관계

이미지가 클수록 공격 표면이 넓다. 불필요한 패키지가 취약점이 된다.

```bash
# 이미지 크기 비교
docker images | grep python
# python:3.11        → 약 920MB (OS 전체 + 빌드 도구)
# python:3.11-slim   → 약 150MB (최소 런타임)
# python:3.11-alpine → 약  50MB (musl libc 기반)
```

### 3.2 베이스 이미지 선택 기준

| 이미지 | 장점 | 단점 | 추천 용도 |
|--------|------|------|----------|
| `ubuntu:22.04` | 익숙함 | 크기 큼 | 개발/테스트 |
| `python:3.11-slim` | 적절한 균형 | 일부 패키지 부족 | 프로덕션 |
| `alpine:3.19` | 매우 작음 | 호환성 문제 가능 | 경량 서비스 |
| `distroless` | 셸 없음, 최소 | 디버깅 어려움 | 보안 중시 환경 |

### 3.3 멀티스테이지 빌드

빌드 도구는 최종 이미지에 포함하지 않는다.

```dockerfile
# Stage 1: 빌드
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: 실행 (빌드 도구 제외)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

---

## 4. 이미지 내 시크릿 탐지

### 4.1 시크릿이 이미지에 남는 경우

```dockerfile
# 위험: 삭제해도 이전 레이어에 남아있음
COPY secret.key /app/
RUN cat /app/secret.key && rm /app/secret.key
```

Docker 이미지는 레이어 구조이므로, 한 레이어에서 파일을 추가하고
다음 레이어에서 삭제해도 **이전 레이어에 그대로 남아있다**.

### 4.2 이미지 히스토리 확인

```bash
# 이미지 빌드 히스토리 확인
docker history nginx:latest

# 특정 레이어의 파일 확인
docker save nginx:latest | tar -xf - -C /tmp/nginx-layers/
ls /tmp/nginx-layers/
```

### 4.3 Trivy로 시크릿 스캔

```bash
# 이미지 내 시크릿 스캔
trivy image --scanners secret nginx:latest

# 파일시스템 시크릿 스캔
trivy fs --scanners secret /path/to/project
```

---

## 5. 실습: web 서버에서 이미지 보안 점검

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: JuiceShop 이미지 취약점 스캔

```bash
ssh student@10.20.30.80

# JuiceShop 이미지 스캔
trivy image bkimminich/juice-shop:latest --severity HIGH,CRITICAL

# 결과에서 CRITICAL 취약점 개수 확인
trivy image bkimminich/juice-shop:latest --severity CRITICAL -f json | \
  python3 -c "import json,sys; d=json.load(sys.stdin); \
  print(sum(len(r.get('Vulnerabilities',[])) for r in d.get('Results',[])))"
```

### 실습 2: 안전한 이미지 vs 위험한 이미지 비교

```bash
# 풀 이미지 스캔
trivy image python:3.11 --severity HIGH,CRITICAL 2>/dev/null | tail -5

# slim 이미지 스캔
trivy image python:3.11-slim --severity HIGH,CRITICAL 2>/dev/null | tail -5

# alpine 이미지 스캔
trivy image python:3.11-alpine --severity HIGH,CRITICAL 2>/dev/null | tail -5
```

### 실습 3: 시크릿이 포함된 이미지 만들고 탐지하기

```bash
# 시크릿 포함 Dockerfile 작성
mkdir -p /tmp/secret-test && cd /tmp/secret-test
cat > secret.key << 'EOF'
-----BEGIN RSA PRIVATE KEY-----
MIIBogIBAAJBALRiMLAHudeSA/fake/key/for/demo/only
-----END RSA PRIVATE KEY-----
EOF

cat > Dockerfile << 'EOF'
FROM alpine:latest
COPY secret.key /app/secret.key
RUN cat /app/secret.key && rm /app/secret.key
CMD ["echo", "hello"]
EOF

# 빌드 및 스캔
docker build -t secret-test .
trivy image --scanners secret secret-test

# 정리
docker rmi secret-test
```

---

## 6. 이미지 보안 자동화

### CI/CD 파이프라인에 Trivy 통합

```bash
# CRITICAL 취약점이 있으면 빌드 실패
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# exit code 0: 통과, 1: 취약점 발견
echo "Exit code: $?"
```

### 이미지 서명 (신뢰 체인)

```bash
# Docker Content Trust 활성화
export DOCKER_CONTENT_TRUST=1

# 서명된 이미지만 pull 가능
docker pull nginx:latest  # 서명 검증 후 다운로드
```

---

## 핵심 정리

1. Docker 이미지에는 취약한 패키지, 시크릿, 악성 코드가 숨어있을 수 있다
2. Trivy로 이미지 스캔하여 CRITICAL/HIGH 취약점을 사전에 발견한다
3. slim/alpine/distroless 등 최소 이미지를 사용하여 공격 표면을 줄인다
4. 멀티스테이지 빌드로 빌드 도구를 최종 이미지에서 제거한다
5. 이미지 레이어에 시크릿이 영구 저장되므로 절대 Dockerfile에 넣지 않는다

---

## 다음 주 예고
- Week 04: 런타임 보안 - 권한 상승, 컨테이너 탈출, --privileged 위험
