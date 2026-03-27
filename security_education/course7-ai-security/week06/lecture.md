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
ssh student@10.20.30.80

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
