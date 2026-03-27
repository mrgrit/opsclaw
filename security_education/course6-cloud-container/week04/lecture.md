# Week 04: 런타임 보안

## 학습 목표
- 컨테이너 런타임의 보안 위협(권한 상승, 탈출)을 이해한다
- `--privileged` 플래그의 위험성을 설명할 수 있다
- Linux capability와 seccomp 프로파일을 활용한 보안 강화를 실습한다
- 컨테이너 탈출 시나리오를 직접 재현하고 방어 방법을 익힌다

---

## 1. 컨테이너 격리의 원리

Docker 컨테이너는 Linux 커널의 3가지 기능으로 격리된다:

| 기술 | 역할 | 예시 |
|------|------|------|
| **Namespace** | 프로세스/네트워크/파일시스템 격리 | PID, NET, MNT |
| **Cgroup** | 리소스 사용량 제한 | CPU, 메모리, I/O |
| **Capability** | root 권한 세분화 | NET_BIND_SERVICE, SYS_ADMIN |

중요: 컨테이너는 호스트 커널을 공유한다. 격리가 깨지면 호스트 전체가 위험해진다.

---

## 2. --privileged의 위험

`--privileged` 플래그는 모든 보안 제한을 해제한다.

```bash
# 절대 프로덕션에서 사용하지 말 것
docker run --privileged -it ubuntu bash
```

### --privileged가 하는 일

- 모든 Linux capability 부여 (약 40개)
- 모든 디바이스(/dev/*) 접근 허용
- seccomp, AppArmor 프로파일 비활성화
- /proc, /sys 쓰기 가능

### --privileged 컨테이너에서 호스트 접근

```bash
# privileged 컨테이너 내부에서
# 호스트 디스크 마운트 가능
mkdir /mnt/host
mount /dev/sda1 /mnt/host
ls /mnt/host  # 호스트 파일시스템 전체 접근!
```

---

## 3. Linux Capabilities

root 권한을 세분화한 것이 capability이다.
컨테이너에 필요한 최소한의 capability만 부여해야 한다.

### 주요 Capability

| Capability | 의미 | 위험도 |
|-----------|------|--------|
| `SYS_ADMIN` | 거의 root 수준 | 매우 높음 |
| `NET_ADMIN` | 네트워크 설정 변경 | 높음 |
| `NET_RAW` | raw 소켓 생성 | 중간 |
| `NET_BIND_SERVICE` | 1024 이하 포트 바인딩 | 낮음 |
| `CHOWN` | 파일 소유자 변경 | 중간 |

### Capability 관리

```bash
# 모든 capability 제거 후 필요한 것만 추가
docker run -d \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --name secure-web \
  nginx:latest

# 컨테이너의 capability 확인
docker inspect --format='{{.HostConfig.CapDrop}}' secure-web
docker inspect --format='{{.HostConfig.CapAdd}}' secure-web
```

---

## 4. Seccomp 프로파일

Seccomp(Secure Computing Mode)은 컨테이너가 호출할 수 있는 시스템콜을 제한한다.

### 기본 seccomp 프로파일

Docker는 기본적으로 약 300개 시스템콜 중 위험한 44개를 차단한다.
차단 목록: `unshare`, `mount`, `reboot`, `kexec_load` 등

```bash
# 기본 seccomp 프로파일 확인
docker inspect --format='{{.HostConfig.SecurityOpt}}' my-container

# 커스텀 seccomp 프로파일 적용
docker run --security-opt seccomp=my-profile.json nginx
```

### 커스텀 프로파일 예시

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat",
                "mmap", "mprotect", "brk", "exit_group"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

---

## 5. 컨테이너 탈출 시나리오

### 5.1 /proc/sysrq-trigger 악용

```bash
# privileged 컨테이너에서
echo b > /proc/sysrq-trigger  # 호스트 즉시 재부팅!
```

### 5.2 Docker 소켓 마운트 악용

```bash
# Docker 소켓이 마운트된 컨테이너
docker run -v /var/run/docker.sock:/var/run/docker.sock ubuntu

# 컨테이너 내부에서 호스트에 새 컨테이너 생성 가능
# (docker CLI 설치 후)
docker run --privileged -v /:/host ubuntu chroot /host
```

### 5.3 cgroup release_agent 탈출

SYS_ADMIN capability가 있으면 cgroup을 통해 호스트에서 명령 실행이 가능하다.

---

## 6. 런타임 보안 강화 방법

### 6.1 읽기 전용 파일시스템

```bash
docker run --read-only \
  --tmpfs /tmp \
  --tmpfs /var/run \
  nginx:latest
```

### 6.2 no-new-privileges

프로세스가 실행 중에 새로운 권한을 얻는 것을 방지한다.

```bash
docker run --security-opt no-new-privileges nginx:latest
```

### 6.3 리소스 제한

```bash
docker run -d \
  --memory=256m \
  --cpus=0.5 \
  --pids-limit=100 \
  nginx:latest
```

---

## 7. 실습: 컨테이너 보안 점검

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: capability 비교

```bash
ssh student@10.20.30.80

# 기본 실행 (기본 capability 포함)
docker run --rm alpine sh -c 'cat /proc/1/status | grep Cap'

# 모든 capability 제거
docker run --rm --cap-drop ALL alpine sh -c 'cat /proc/1/status | grep Cap'

# CapEff 값을 capsh로 해독
docker run --rm alpine sh -c \
  'apk add -q libcap && capsh --decode=00000000a80425fb'
```

### 실습 2: 읽기 전용 vs 쓰기 가능

```bash
# 쓰기 가능 컨테이너 (기본)
docker run --rm alpine sh -c 'echo hacked > /etc/passwd; echo "성공"'

# 읽기 전용 컨테이너
docker run --rm --read-only alpine sh -c 'echo hacked > /etc/passwd; echo "성공"'
# 결과: Read-only file system 에러
```

### 실습 3: Docker 소켓 노출 위험 확인

```bash
# 절대 프로덕션에서 하지 말 것 (학습 목적만)
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  docker:cli docker ps
# 컨테이너 내부에서 호스트의 모든 컨테이너 조회 가능!
```

---

## 8. 보안 점검 체크리스트

- [ ] `--privileged` 사용하지 않는가?
- [ ] `--cap-drop ALL` 후 필요한 것만 추가했는가?
- [ ] `--read-only` 파일시스템을 사용하는가?
- [ ] `--security-opt no-new-privileges` 적용했는가?
- [ ] Docker 소켓을 마운트하지 않는가?
- [ ] 메모리/CPU/PID 제한을 설정했는가?

---

## 핵심 정리

1. `--privileged`는 모든 보안 장벽을 해제하므로 절대 사용하지 않는다
2. `--cap-drop ALL` 후 필요한 capability만 `--cap-add`로 추가한다
3. Seccomp 프로파일로 불필요한 시스템콜을 차단한다
4. Docker 소켓 마운트는 호스트 전체 제어 권한을 넘겨주는 것과 같다
5. 읽기 전용 파일시스템 + no-new-privileges로 기본 방어선을 구축한다

---

## 다음 주 예고
- Week 05: Docker 네트워크 보안 - 네트워크 격리, 포트 노출, 컨테이너 간 통신 제어
