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
ssh student@10.20.30.80

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
