# Week 07: Docker 보안 점검

## 학습 목표
- CIS Docker Benchmark의 주요 항목을 이해한다
- Docker Bench for Security 도구를 실행하고 결과를 해석할 수 있다
- 점검 결과를 바탕으로 보안 개선 조치를 수행할 수 있다

---

## 1. CIS Docker Benchmark란?

CIS(Center for Internet Security)에서 발행한 Docker 보안 설정 가이드이다.
호스트, 데몬, 이미지, 컨테이너, 네트워크 등 7개 영역을 점검한다.

### 7대 점검 영역

| 영역 | 내용 | 예시 |
|------|------|------|
| 1. 호스트 설정 | OS 보안, 파티션 | /var/lib/docker 별도 파티션 |
| 2. Docker 데몬 | 데몬 보안 설정 | TLS 인증, 로깅 드라이버 |
| 3. Docker 데몬 파일 | 파일 권한 | docker.sock 권한 660 |
| 4. 컨테이너 이미지 | 이미지 보안 | 신뢰할 수 있는 베이스 이미지 |
| 5. 컨테이너 런타임 | 실행 시 보안 | privileged 비사용 |
| 6. Docker Security Operations | 운영 보안 | 정기 점검, 패치 관리 |
| 7. Docker Swarm | 오케스트레이션 | 인증서, 암호화 |

---

## 2. Docker Bench for Security

CIS Benchmark를 자동으로 점검하는 오픈소스 스크립트이다.

### 2.1 실행 방법

```bash
# 방법 1: Docker로 실행 (권장)
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /etc:/etc:ro \
  docker/docker-bench-security

# 방법 2: 스크립트 직접 실행
git clone https://github.com/docker/docker-bench-security.git
cd docker-bench-security
sudo sh docker-bench-security.sh
```

### 2.2 결과 해석

```
[INFO] 1 - Host Configuration
[PASS] 1.1 - Ensure a separate partition for containers has been created
[WARN] 1.2 - Ensure only trusted users are allowed to control Docker daemon

[INFO] 5 - Container Runtime
[WARN] 5.1 - Ensure that, if applicable, an AppArmor Profile is enabled
[PASS] 5.2 - Ensure that, if applicable, SELinux security options are set
[WARN] 5.3 - Ensure that Linux kernel capabilities are restricted
[WARN] 5.4 - Ensure that privileged containers are not used
```

결과 분류:
- **[PASS]**: 보안 기준 충족
- **[WARN]**: 개선 필요
- **[NOTE]**: 정보성 메시지
- **[INFO]**: 섹션 구분

---

## 3. 주요 점검 항목 상세

### 3.1 데몬 보안 (섹션 2)

```bash
# 2.1 - 로깅 드라이버 설정 확인
docker info --format '{{.LoggingDriver}}'
# 권장: json-file 또는 journald

# 2.2 - live-restore 활성화 확인
docker info --format '{{.LiveRestoreEnabled}}'
# 데몬 재시작 시 컨테이너 유지

# daemon.json 보안 설정
cat /etc/docker/daemon.json
```

### 권장 daemon.json

```json
{
  "icc": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true,
  "userland-proxy": false,
  "no-new-privileges": true,
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Hard": 64000, "Soft": 64000 }
  }
}
```

### 3.2 파일 권한 (섹션 3)

```bash
# docker.sock 권한 확인 (660 이하여야 함)
ls -l /var/run/docker.sock

# Docker 관련 파일 권한 점검
ls -l /etc/docker/
ls -l /var/lib/docker/

# docker.service 파일 권한
ls -l /usr/lib/systemd/system/docker.service
```

### 3.3 컨테이너 런타임 (섹션 5)

```bash
# 모든 컨테이너의 보안 설정 한 번에 확인
for c in $(docker ps -q); do
  echo "=== $(docker inspect --format='{{.Name}}' $c) ==="
  echo "User: $(docker inspect --format='{{.Config.User}}' $c)"
  echo "Privileged: $(docker inspect --format='{{.HostConfig.Privileged}}' $c)"
  echo "ReadOnly: $(docker inspect --format='{{.HostConfig.ReadonlyRootfs}}' $c)"
  echo "CapDrop: $(docker inspect --format='{{.HostConfig.CapDrop}}' $c)"
  echo "PidsLimit: $(docker inspect --format='{{.HostConfig.PidsLimit}}' $c)"
  echo ""
done
```

---

## 4. 자동 점검 스크립트 작성

### 4.1 간단한 보안 점검 스크립트

```bash
#!/bin/bash
# docker-security-check.sh

echo "=== Docker 보안 간이 점검 ==="
echo ""

# 1. Docker 버전
echo "[점검] Docker 버전"
docker version --format '서버: {{.Server.Version}}'

# 2. root로 실행되는 컨테이너
echo ""
echo "[점검] root 실행 컨테이너"
for c in $(docker ps -q); do
  user=$(docker inspect --format='{{.Config.User}}' $c)
  name=$(docker inspect --format='{{.Name}}' $c)
  if [ -z "$user" ] || [ "$user" = "root" ]; then
    echo "  [WARN] $name → root로 실행 중"
  else
    echo "  [PASS] $name → $user"
  fi
done

# 3. privileged 컨테이너
echo ""
echo "[점검] Privileged 컨테이너"
for c in $(docker ps -q); do
  priv=$(docker inspect --format='{{.HostConfig.Privileged}}' $c)
  name=$(docker inspect --format='{{.Name}}' $c)
  if [ "$priv" = "true" ]; then
    echo "  [WARN] $name → privileged!"
  else
    echo "  [PASS] $name → 비특권"
  fi
done

# 4. 네트워크 모드
echo ""
echo "[점검] host 네트워크 사용 컨테이너"
for c in $(docker ps -q); do
  net=$(docker inspect --format='{{.HostConfig.NetworkMode}}' $c)
  name=$(docker inspect --format='{{.Name}}' $c)
  if [ "$net" = "host" ]; then
    echo "  [WARN] $name → host 네트워크"
  fi
done

echo ""
echo "=== 점검 완료 ==="
```

---

## 5. 실습: Docker Bench 실행

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: Docker Bench 실행

```bash
ssh student@10.20.30.80

# Docker Bench 실행
docker run --rm --net host --pid host --userns host \
  --cap-add audit_control \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /etc:/etc:ro \
  docker/docker-bench-security 2>&1 | tee /tmp/bench-result.txt

# WARN 개수 확인
grep -c "\[WARN\]" /tmp/bench-result.txt

# 섹션별 WARN 요약
for i in 1 2 3 4 5 6 7; do
  count=$(grep "^\[WARN\] $i\." /tmp/bench-result.txt | wc -l)
  echo "섹션 $i: WARN $count건"
done
```

### 실습 2: WARN 항목 개선

```bash
# 예: 로그 크기 제한이 없는 경우
# daemon.json에 로그 설정 추가
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# Docker 데몬 재시작
sudo systemctl restart docker
```

### 실습 3: 간이 점검 스크립트 실행

```bash
# 위의 docker-security-check.sh를 작성하고 실행
chmod +x /tmp/docker-security-check.sh
bash /tmp/docker-security-check.sh
```

---

## 6. 점검 결과 보고서 작성

보안 점검 보고서에는 다음 내용을 포함한다:

1. **점검 일시**: 언제 점검했는가
2. **점검 대상**: 어떤 서버/컨테이너를 점검했는가
3. **발견 사항**: WARN 항목 목록과 심각도
4. **개선 조치**: 각 WARN에 대한 수정 방법
5. **후속 계획**: 다음 점검 일정

---

## 핵심 정리

1. CIS Docker Benchmark는 7개 영역의 보안 설정 기준을 제공한다
2. Docker Bench for Security로 자동 점검을 수행한다
3. daemon.json으로 데몬 수준의 보안 설정을 일괄 적용한다
4. 정기적인 점검과 보고서 작성이 운영 보안의 핵심이다
5. [WARN] 항목을 하나씩 개선하여 보안 수준을 높인다

---

## 다음 주 예고
- Week 08: 중간고사 - Docker 보안 강화 실전 과제
