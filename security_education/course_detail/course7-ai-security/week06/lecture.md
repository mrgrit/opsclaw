# Week 06: 취약점 분석 (상세 버전)

## 학습 목표
- LLM을 활용한 소스 코드 보안 리뷰 방법을 익힌다
- CVE 정보를 LLM으로 분석하고 영향을 평가할 수 있다
- 취약점 보고서를 자동 생성할 수 있다
- LLM 기반 취약점 분석의 한계를 이해한다


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

## 용어 해설 (AI/LLM 보안 활용 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **LLM** | Large Language Model | 대규모 언어 모델 (GPT, Claude, Llama 등) | 방대한 텍스트로 훈련된 AI 두뇌 |
| **Ollama** | Ollama | 로컬에서 LLM을 실행하는 도구 | 내 PC에서 돌리는 AI |
| **프롬프트** | Prompt | LLM에게 보내는 입력 텍스트 | AI에게 하는 질문/지시 |
| **토큰** | Token (LLM) | LLM이 처리하는 텍스트의 최소 단위 (~4글자) | 단어의 조각 |
| **컨텍스트 윈도우** | Context Window | LLM이 한 번에 처리할 수 있는 최대 토큰 수 | AI의 단기 기억 용량 |
| **파인튜닝** | Fine-tuning | 사전 학습된 모델을 특정 목적에 맞게 추가 학습 | 일반의가 전공 수련 |
| **RAG** | Retrieval-Augmented Generation | 외부 데이터를 검색하여 LLM 응답에 반영 | AI가 자료를 찾아보고 답변 |
| **에이전트** | Agent (AI) | 도구를 사용하여 자율적으로 작업하는 AI 시스템 | AI 비서 (스스로 판단하고 실행) |
| **도구 호출** | Tool Calling | LLM이 외부 도구/API를 호출하는 기능 | AI가 계산기를 꺼내서 계산 |
| **하네스** | Harness | 에이전트를 관리·제어하는 프레임워크 | AI 비서의 업무 규칙·관리 시스템 |
| **Playbook** | Playbook | 자동화된 작업 절차 (도구/스킬의 순서화된 묶음) | 표준 작업 지침서 (SOP) |
| **PoW** | Proof of Work | 작업 증명 (해시 체인 기반 실행 기록) | 작업 일지 + 영수증 |
| **보상** | Reward (RL) | 태스크 실행 결과에 따른 점수 (+성공, -실패) | 성과급 |
| **Q-learning** | Q-learning | 보상을 기반으로 최적 행동을 학습하는 RL 알고리즘 | 시행착오로 최적 경로를 찾는 학습 |
| **UCB1** | Upper Confidence Bound | 탐험(exploration)과 활용(exploitation)을 균형 잡는 전략 | "가본 길 vs 안 가본 길" 선택 전략 |
| **SubAgent** | SubAgent | 대상 서버에서 명령을 실행하는 경량 런타임 | 현장 파견 직원 |


---

# Week 06: 취약점 분석

## 학습 목표
- LLM을 활용한 소스 코드 보안 리뷰 방법을 익힌다
- CVE 정보를 LLM으로 분석하고 영향을 평가할 수 있다
- 취약점 보고서를 자동 생성할 수 있다
- LLM 기반 취약점 분석의 한계를 이해한다

---

## 1. 전통적 취약점 분석 vs LLM 보조

| 항목 | 전통적 방법 | LLM 보조 |
|------|-----------|---------|
| 코드 리뷰 | 전문가 수동 검토 | LLM이 패턴 탐지 후 전문가 확인 |
| CVE 분석 | NVD 데이터베이스 조회 | LLM이 영향 평가 및 요약 |
| 보고서 | 수동 작성 | LLM이 초안 생성 |
| 속도 | 느림 | 빠름 |
| 정확도 | 높음 | 검증 필요 |

---

## 2. LLM 기반 코드 보안 리뷰

> **이 실습을 왜 하는가?**
> AI/LLM 보안 활용 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> AI 보안 자동화에서 이 기법은 로그 분석, 룰 생성, 대응 실행을 LLM이 수행하는 기반이다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.


### 2.1 Python 코드 취약점 탐지

```bash
CODE='
from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.route("/user")
def get_user():
    user_id = request.args.get("id")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return str(cursor.fetchall())

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    file.save(f"/uploads/{file.filename}")
    return "uploaded"

@app.route("/run")
def run_cmd():
    import os
    cmd = request.args.get("cmd")
    result = os.popen(cmd).read()
    return result
'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"보안 코드 리뷰어입니다. 코드의 보안 취약점을 찾아 다음 형식으로 보고하세요:\\n1. 취약점명\\n2. CWE 번호\\n3. 위치 (함수/라인)\\n4. 심각도 (CRITICAL/HIGH/MEDIUM/LOW)\\n5. 설명\\n6. 수정된 코드\"},
      {\"role\": \"user\", \"content\": \"다음 Python Flask 코드의 보안 취약점을 모두 찾아주세요:\\n$CODE\"}
    ],
    \"temperature\": 0.2
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 2.2 설정 파일 보안 검토

```bash
CONFIG='
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
    }

    location /admin {
        proxy_pass http://backend:5000/admin;
    }

    autoindex on;
    server_tokens on;
}
'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"nginx 보안 전문가입니다.\"},
      {\"role\": \"user\", \"content\": \"이 nginx 설정의 보안 문제를 찾고 수정하세요:\\n$CONFIG\"}
    ],
    \"temperature\": 0.2
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 3. CVE 분석

### 3.1 CVE 정보 분석 및 요약

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "취약점 분석가입니다. CVE 정보를 분석하여 실무자가 바로 대응할 수 있는 보고서를 작성하세요."},
      {"role": "user", "content": "CVE-2024-3094 (xz-utils 백도어)를 분석해주세요.\n\n다음 형식으로:\n1. 한 줄 요약\n2. 영향 범위 (어떤 시스템이 위험한가)\n3. CVSS 점수 및 위험도 설명\n4. 공격 방법 (단순화하여)\n5. 즉시 대응 방법\n6. 장기 대응 방법\n7. 우리 환경(Ubuntu 22.04) 영향 여부 확인 명령어"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 3.2 영향 범위 분석

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "취약점 영향 분석 전문가입니다."},
      {"role": "user", "content": "다음 서버 환경에서 CVE-2021-44228(Log4Shell)의 영향을 분석하세요:\n\n서버 목록:\n1. web (Ubuntu 22.04, nginx + Node.js)\n2. secu (Ubuntu 22.04, nftables + Suricata)\n3. siem (Ubuntu 22.04, Wazuh 4.11.2)\n4. dgx-spark (Ubuntu, Python + Ollama)\n\n각 서버별로 영향 여부와 확인 방법을 알려주세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. 취약점 보고서 자동 생성

### 4.1 스캔 결과를 보고서로 변환

```bash
SCAN_RESULT='
취약점 스캔 결과 (Trivy):
1. CVE-2023-44487 (HTTP/2 Rapid Reset) - CRITICAL - nginx:1.24
2. CVE-2023-5678 (OpenSSL) - HIGH - libssl3
3. CVE-2024-1234 (glibc) - MEDIUM - libc6
4. CVE-2023-9999 (zlib) - LOW - zlib1g
'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"취약점 관리 전문가입니다. 스캔 결과를 경영진용 보고서로 변환합니다.\"},
      {\"role\": \"user\", \"content\": \"다음 스캔 결과를 보고서로 변환하세요. 각 취약점에 대해 비즈니스 영향, 패치 우선순위, 예상 소요 시간을 포함하세요:\\n$SCAN_RESULT\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 실습

### 실습 1: JuiceShop 코드 취약점 분석

```bash
# JuiceShop은 의도적으로 취약한 웹 앱이다
# LLM으로 대표적인 취약점 패턴을 분석

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "웹 애플리케이션 보안 전문가입니다."},
      {"role": "user", "content": "OWASP JuiceShop 웹 앱(Node.js/Express)에서 흔히 발견되는 취약점 5가지를 설명하고, 각각에 대해:\n1. 취약한 코드 패턴\n2. 공격 방법\n3. 안전한 코드로의 수정\n을 보여주세요."}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 2: Docker 이미지 취약점 분석

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

# Trivy 스캔 결과를 LLM으로 분석
TRIVY_OUT=$(trivy image --severity CRITICAL nginx:latest -f json 2>/dev/null | head -500)

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"취약점 분석가입니다. Trivy 스캔 결과를 분석하여 패치 우선순위를 정해주세요.\"},
      {\"role\": \"user\", \"content\": \"Trivy 스캔 결과를 분석하세요. 패치 우선순위와 대응 방안을 제시해주세요.\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: 수정 코드 생성

```bash
VULN_CODE='
import subprocess

def ping_host(host):
    # 사용자 입력을 직접 명령어에 삽입
    result = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True)
    return result.stdout.decode()
'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"시큐어 코딩 전문가입니다. 취약한 코드를 분석하고 안전한 대체 코드를 제공하세요.\"},
      {\"role\": \"user\", \"content\": \"이 코드의 취약점과 수정 코드를 보여주세요:\\n$VULN_CODE\"}
    ],
    \"temperature\": 0.2
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. LLM 취약점 분석의 한계

1. **오탐/미탐**: LLM이 취약점을 놓치거나 잘못 판단할 수 있다
2. **컨텍스트 제한**: 대규모 코드베이스를 한 번에 분석할 수 없다
3. **최신 CVE**: 학습 데이터 이후의 CVE를 모를 수 있다
4. **깊은 분석**: 복잡한 로직 취약점(비즈니스 로직 결함)은 탐지 어려움
5. **검증 필수**: LLM 결과는 반드시 전문가가 검증해야 한다

### 올바른 활용 방법

```
LLM의 역할: 1차 필터링 + 초안 작성 + 교육 보조
전문가 역할: 최종 판단 + 심층 분석 + 비즈니스 로직 검증
```

---

## 핵심 정리

1. LLM은 코드 리뷰에서 일반적인 취약점 패턴을 빠르게 식별한다
2. CVE 정보를 LLM으로 분석하여 영향 평가와 대응 방안을 도출한다
3. Trivy 등 스캐너 결과를 LLM으로 해석하여 우선순위를 결정한다
4. 취약점 보고서 초안을 LLM으로 자동 생성할 수 있다
5. LLM은 보조 도구이며, 최종 판단은 전문가가 내린다

---

## 다음 주 예고
- Week 07: AI 에이전트 아키텍처 - Master-Manager-SubAgent 구조


---

---

## 심화: AI/LLM 보안 활용 보충

### Ollama API 상세 가이드

#### 기본 호출 구조

```bash
# Ollama는 OpenAI 호환 API를 제공한다
# URL: http://192.168.0.105:11434/v1/chat/completions

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",        ← 사용할 모델
    "messages": [
      {"role": "system", "content": "역할 부여"},  ← 시스템 프롬프트
      {"role": "user", "content": "실제 질문"}      ← 사용자 입력
    ],
    "temperature": 0.1,            ← 출력 다양성 (0=결정론, 1=창의적)
    "max_tokens": 1000             ← 최대 출력 길이
  }'
```

> **각 파라미터의 의미:**
> - `model`: 어떤 AI 모델을 사용할지. 큰 모델일수록 정확하지만 느림
> - `messages`: 대화 내역. system(역할)→user(질문)→assistant(답변) 순서
> - `temperature`: 0에 가까우면 같은 질문에 항상 같은 답. 1에 가까우면 매번 다른 답
> - `max_tokens`: 출력 길이 제한. 토큰 ≈ 글자 수 × 0.5 (한국어)

#### 모델별 특성

| 모델 | 크기 | 응답 시간 | 정확도 | 권장 용도 |
|------|------|---------|--------|---------|
| gemma3:12b | 12B | ~5초 | 양호 | 분석, 룰 생성, 보고서 |
| llama3.1:8b | 8B | ~3초 | 보통 | 빠른 분류, 검증 |
| qwen3:8b | 8B | ~5초 | 보통 | 교차 검증 (다른 벤더) |
| gpt-oss:120b | 120B | ~25초 | 높음 | 복잡한 분석 (시간 여유 시) |

#### 프롬프트 엔지니어링 패턴

**패턴 1: 역할 부여 (Role Assignment)**
```json
{"role":"system","content":"당신은 10년 경력의 SOC 분석가입니다. MITRE ATT&CK에 정통합니다."}
```

**패턴 2: 출력 형식 강제 (Format Control)**
```json
{"role":"system","content":"반드시 JSON으로만 응답하세요. 마크다운, 설명, 주석을 포함하지 마세요."}
```

**패턴 3: Few-shot (예시 제공)**
```json
{"role":"user","content":"예시:\n입력: SSH 실패 5회\n출력: {\"severity\":\"HIGH\",\"attack\":\"brute_force\"}\n\n이제 분석하세요: SSH 실패 20회 후 성공"}
```

**패턴 4: Chain of Thought (단계별 사고)**
```json
{"role":"system","content":"단계별로 분석하세요: 1)현상 파악 2)원인 추론 3)ATT&CK 매핑 4)대응 방안"}
```

### OpsClaw API 핵심 흐름 요약

```
[1] POST /projects                     → 프로젝트 생성
    Body: {"name":"...", "master_mode":"external"}
    Response: {"project":{"id":"prj_xxx"}}

[2] POST /projects/{id}/plan           → plan 단계로 전환
[3] POST /projects/{id}/execute        → execute 단계로 전환

[4] POST /projects/{id}/execute-plan   → 태스크 실행
    Body: {"tasks":[...], "parallel":true, "subagent_url":"..."}
    Response: {"overall":"success", "tasks_ok":N}

[5] GET /projects/{id}/evidence/summary → 증적 확인
[6] GET /projects/{id}/replay           → 타임라인 재구성
[7] POST /projects/{id}/completion-report → 완료 보고

모든 API에 필수: -H "X-API-Key: opsclaw-api-key-2026"
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 06: 취약점 분석"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **AI/LLM 보안 활용의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 전통적 취약점 분석 vs LLM 보조"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. LLM 기반 코드 보안 리뷰"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **AI/LLM 보안 활용 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. CVE 분석"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 LLM/OpsClaw의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 AI/LLM 보안 활용 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---
