# Week 02: Docker 기초 + 보안

## 학습 목표
- Docker의 핵심 개념(이미지, 컨테이너, 네트워크, 볼륨)을 이해한다
- Dockerfile을 작성하고 보안 관점에서 점검할 수 있다
- 컨테이너 기반 환경의 보안 이점과 위험을 설명할 수 있다

---

## 1. Docker란 무엇인가?

Docker는 애플리케이션을 **컨테이너**라는 격리된 환경에서 실행하는 기술이다.
가상머신(VM)과 달리 OS 커널을 공유하므로 가볍고 빠르다.

### VM vs 컨테이너 비교

| 항목 | 가상머신 | 컨테이너 |
|------|---------|---------|
| 부팅 시간 | 분 단위 | 초 단위 |
| 크기 | GB | MB |
| 격리 수준 | 하드웨어 수준 | 프로세스 수준 |
| 보안 격리 | 강함 | 상대적으로 약함 |

---

## 2. Docker 핵심 구성요소

### 2.1 이미지 (Image)
컨테이너를 만들기 위한 읽기 전용 템플릿이다. 여러 **레이어**로 구성된다.

```bash
# 이미지 다운로드
docker pull nginx:latest

# 로컬 이미지 목록
docker images
```

### 2.2 컨테이너 (Container)
이미지를 실행한 인스턴스이다. 격리된 파일시스템, 네트워크, 프로세스를 가진다.

```bash
# 컨테이너 실행
docker run -d --name my-nginx -p 8080:80 nginx:latest

# 실행 중인 컨테이너 확인
docker ps

# 컨테이너 내부 접속
docker exec -it my-nginx /bin/bash
```

### 2.3 네트워크 (Network)
컨테이너 간 통신을 제어한다. 기본적으로 bridge, host, none 네트워크가 있다.

```bash
# 네트워크 목록
docker network ls

# 사용자 정의 네트워크 생성
docker network create my-secure-net
```

### 2.4 볼륨 (Volume)
컨테이너 데이터를 영구 저장하는 방법이다. 컨테이너가 삭제되어도 데이터가 유지된다.

```bash
# 볼륨 생성
docker volume create my-data

# 볼륨 마운트하여 실행
docker run -d -v my-data:/app/data nginx:latest
```

---

## 3. Dockerfile 작성

Dockerfile은 이미지를 빌드하기 위한 명령어 모음이다.

```dockerfile
# 기본 이미지 지정
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 비root 사용자로 전환
RUN useradd -m appuser
USER appuser

# 포트 노출
EXPOSE 8000

# 실행 명령
CMD ["python", "app.py"]
```

---

## 4. Dockerfile 보안 베스트 프랙티스

### 4.1 비root 사용자 사용
```dockerfile
# 나쁜 예: root로 실행 (기본값)
CMD ["python", "app.py"]

# 좋은 예: 전용 사용자 생성
RUN useradd -r -s /bin/false appuser
USER appuser
CMD ["python", "app.py"]
```

### 4.2 최소 이미지 사용
```dockerfile
# 나쁜 예: 전체 이미지 (900MB+)
FROM python:3.11

# 좋은 예: slim 이미지 (150MB)
FROM python:3.11-slim

# 최적: distroless (셸 없음)
FROM gcr.io/distroless/python3
```

### 4.3 COPY 대신 ADD 피하기
```dockerfile
# 나쁜 예: ADD는 URL 다운로드, tar 자동 압축해제 기능이 있어 위험
ADD https://example.com/app.tar.gz /app/

# 좋은 예: COPY는 단순 파일 복사만 수행
COPY app.tar.gz /app/
```

### 4.4 시크릿을 이미지에 넣지 않기
```dockerfile
# 절대 금지: 비밀번호가 이미지 레이어에 영구 저장됨
ENV DB_PASSWORD=mysecret123

# 올바른 방법: 실행 시 환경변수로 전달
# docker run -e DB_PASSWORD=mysecret123 myapp
```

---

## 5. 실습: web 서버에서 Docker 다루기

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: 컨테이너 기본 조작

```bash
# web 서버 접속 후 실행 중인 컨테이너 확인
ssh student@10.20.30.80
docker ps

# JuiceShop 컨테이너 확인
docker inspect bunkerweb-juiceshop-1 | head -50
```

### 실습 2: 보안 관점 컨테이너 점검

```bash
# 컨테이너가 root로 실행 중인지 확인
docker inspect --format='{{.Config.User}}' bunkerweb-juiceshop-1

# 컨테이너의 capability 확인
docker inspect --format='{{.HostConfig.CapAdd}}' bunkerweb-juiceshop-1

# 읽기 전용 파일시스템 여부 확인
docker inspect --format='{{.HostConfig.ReadonlyRootfs}}' bunkerweb-juiceshop-1
```

### 실습 3: 안전한 컨테이너 실행

```bash
# 보안 옵션 적용하여 nginx 실행
docker run -d \
  --name secure-nginx \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /var/cache/nginx \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  -u 1000:1000 \
  -p 9090:80 \
  nginx:latest

# 정상 작동 확인
curl http://localhost:9090
```

---

## 6. 보안 체크리스트

Docker 컨테이너를 배포할 때 최소한 아래 항목을 점검하라:

- [ ] root 사용자로 실행하지 않는가?
- [ ] 불필요한 capability를 제거했는가?
- [ ] 읽기 전용 파일시스템을 사용하는가?
- [ ] 최소 이미지(slim/alpine/distroless)를 사용하는가?
- [ ] 이미지에 시크릿이 포함되어 있지 않은가?
- [ ] 불필요한 포트를 노출하지 않는가?

---

## 핵심 정리

1. Docker는 가볍고 빠르지만 VM보다 격리 수준이 낮다
2. 이미지, 컨테이너, 네트워크, 볼륨이 4대 핵심 요소이다
3. Dockerfile 작성 시 비root 실행, 최소 이미지, 시크릿 미포함이 필수이다
4. `--read-only`, `--cap-drop ALL` 등으로 런타임 보안을 강화한다

---

## 다음 주 예고
- Week 03: 이미지 보안 - Trivy를 활용한 취약점 스캐닝
