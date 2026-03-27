# Week 11: Kubernetes 보안 기초

## 학습 목표
- Kubernetes(K8s)의 기본 구조와 보안 관련 구성요소를 이해한다
- Pod Security Standards를 적용할 수 있다
- RBAC(Role-Based Access Control)으로 접근을 제어할 수 있다
- NetworkPolicy로 Pod 간 통신을 제한할 수 있다

---

## 1. Kubernetes 기본 구조

### 1.1 주요 구성요소

```
Control Plane (마스터)
├── API Server      ← 모든 요청의 진입점
├── etcd            ← 클러스터 상태 저장소
├── Scheduler       ← Pod 배치 결정
└── Controller      ← 상태 유지 관리

Worker Node
├── kubelet         ← Pod 관리 에이전트
├── kube-proxy      ← 네트워크 프록시
└── Container Runtime (Docker/containerd)
```

### 1.2 보안 관점 핵심 개념

| 개념 | 설명 | 보안 의미 |
|------|------|----------|
| **Pod** | 최소 배포 단위 (1+ 컨테이너) | 격리 단위 |
| **ServiceAccount** | Pod의 ID | API 서버 접근 권한 |
| **Namespace** | 논리적 분리 | 리소스 격리 |
| **Secret** | 비밀정보 저장 | 암호화 필요 |

---

## 2. Pod Security Standards

Kubernetes는 3가지 보안 수준을 정의한다.

### 2.1 세 가지 보안 수준

| 수준 | 설명 | 제한 |
|------|------|------|
| **Privileged** | 제한 없음 | 모든 설정 허용 |
| **Baseline** | 알려진 위험 차단 | privileged, hostNetwork 등 차단 |
| **Restricted** | 최대 보안 | non-root, read-only, 최소 capability |

### 2.2 안전한 Pod 정의

```yaml
# secure-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
spec:
  securityContext:
    runAsNonRoot: true           # root 실행 금지
    runAsUser: 1000              # UID 1000으로 실행
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault       # 기본 seccomp 프로파일
  containers:
    - name: app
      image: myapp:v1.0
      securityContext:
        allowPrivilegeEscalation: false  # 권한 상승 금지
        readOnlyRootFilesystem: true     # 읽기 전용
        capabilities:
          drop: ["ALL"]                  # 모든 capability 제거
      resources:
        limits:
          memory: "256Mi"
          cpu: "500m"
        requests:
          memory: "128Mi"
          cpu: "250m"
      volumeMounts:
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: tmp
      emptyDir: {}
  automountServiceAccountToken: false   # 불필요 시 SA 토큰 마운트 안 함
```

### 2.3 위험한 Pod 설정

```yaml
# 절대 사용하지 말 것
spec:
  hostNetwork: true          # 호스트 네트워크 공유 → 모든 트래픽 접근
  hostPID: true              # 호스트 PID 공유 → 호스트 프로세스 조회
  containers:
    - name: bad
      securityContext:
        privileged: true      # 호스트 전체 접근
        runAsUser: 0          # root 실행
```

---

## 3. RBAC (Role-Based Access Control)

### 3.1 RBAC 구성요소

```
Role/ClusterRole          → 무엇을 할 수 있는가 (권한 정의)
RoleBinding/ClusterRoleBinding → 누구에게 부여하는가 (권한 연결)
```

| 리소스 | 범위 | 용도 |
|--------|------|------|
| Role | Namespace 내 | 특정 네임스페이스 권한 |
| ClusterRole | 클러스터 전체 | 전체 클러스터 권한 |
| RoleBinding | Namespace 내 | Role을 사용자에 연결 |
| ClusterRoleBinding | 클러스터 전체 | ClusterRole을 사용자에 연결 |

### 3.2 RBAC 예시

```yaml
# 읽기 전용 Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
---
# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: production
  name: read-pods
subjects:
  - kind: ServiceAccount
    name: monitoring-sa
    namespace: production
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### 3.3 위험한 RBAC 패턴

```yaml
# 절대 금지: 와일드카드 권한
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]

# 위험: secrets 접근 권한
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]
    # → 클러스터의 모든 비밀정보 조회 가능
```

---

## 4. NetworkPolicy

Pod 간 네트워크 통신을 제어하는 방화벽 역할이다.
기본적으로 모든 Pod는 서로 통신 가능하다.

### 4.1 기본 거부 정책

```yaml
# 모든 인바운드 트래픽 차단
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}     # 모든 Pod에 적용
  policyTypes:
    - Ingress         # 인바운드 차단 (아웃바운드는 허용)
```

### 4.2 선택적 허용

```yaml
# web → api만 허용
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api           # api Pod에 적용
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: web   # web Pod에서만 허용
      ports:
        - protocol: TCP
          port: 8080
```

### 4.3 네트워크 격리 패턴

```
[인터넷] → [Ingress] → [web Pod] → [api Pod] → [db Pod]
                         frontend    backend     database
                         네트워크     네트워크     네트워크
```

---

## 5. Kubernetes Secret 보안

### 5.1 Secret의 문제점

```bash
# Secret은 기본적으로 Base64 인코딩일 뿐 (암호화 아님!)
echo "cGFzc3dvcmQxMjM=" | base64 -d
# → password123
```

### 5.2 Secret 보안 강화

1. **etcd 암호화**: Secret을 저장할 때 암호화
2. **RBAC 제한**: Secret 접근 권한을 최소화
3. **외부 관리**: HashiCorp Vault, AWS Secrets Manager 사용
4. **환경변수 대신 파일**: volumeMount로 파일로 전달

---

## 6. 실습: Docker Compose로 K8s 개념 체험

실습 환경: `web` 서버 (10.20.30.80)

### 실습 1: RBAC 개념을 Docker 환경에서 이해

```bash
ssh student@10.20.30.80

# Docker에서의 접근 제어 = docker.sock 접근 권한
# K8s에서의 접근 제어 = RBAC

# Docker 그룹에 속한 사용자만 Docker 명령 사용 가능
groups  # docker 그룹 확인
```

### 실습 2: NetworkPolicy를 nftables로 시뮬레이션

```bash
# secu 서버에서 Pod 간 통신 제어 개념 이해
ssh student@10.20.30.1

# web(10.20.30.80)에서 siem(10.20.30.100)으로의 특정 포트만 허용
# 이것이 K8s NetworkPolicy의 원리
sudo nft list ruleset | head -30
```

### 실습 3: LLM으로 K8s 보안 설정 분석

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Kubernetes 보안 전문가로서 YAML 설정을 분석해주세요."},
      {"role": "user", "content": "다음 Pod 설정의 보안 문제를 찾아주세요:\napiVersion: v1\nkind: Pod\nspec:\n  containers:\n  - name: app\n    image: myapp\n    securityContext:\n      privileged: true\n      runAsUser: 0\n  hostNetwork: true\n  hostPID: true"}
    ]
  }' | python3 -m json.tool
```

---

## 7. K8s 보안 체크리스트

- [ ] Pod Security Standards (Restricted) 적용했는가?
- [ ] 모든 컨테이너가 non-root로 실행되는가?
- [ ] RBAC이 최소 권한으로 설정되어 있는가?
- [ ] default NetworkPolicy(deny all)가 적용되어 있는가?
- [ ] Secret이 etcd에서 암호화되는가?
- [ ] ServiceAccount 토큰 자동 마운트를 비활성화했는가?
- [ ] 리소스 limits가 설정되어 있는가?

---

## 핵심 정리

1. Pod Security Standards의 Restricted 수준을 기본으로 적용한다
2. RBAC은 최소 권한 원칙으로 설정하고, 와일드카드(*)를 절대 사용하지 않는다
3. NetworkPolicy로 Pod 간 통신을 명시적으로 허용한 것만 가능하게 한다
4. Secret은 Base64일 뿐이므로 etcd 암호화 + RBAC 제한이 필수이다
5. ServiceAccount 토큰 자동 마운트는 불필요 시 비활성화한다

---

## 다음 주 예고
- Week 12: Kubernetes 공격 - Pod 탈출, ServiceAccount 악용
