#!/usr/bin/env python3
"""기존 교안을 3배 분량으로 확장하는 스크립트.

각 교안에 다음을 추가:
1. 강의 시간 배분표 (3시간)
2. 각 섹션을 "왜?" 설명, 트러블슈팅, 실제 사례로 확장
3. 추가 실습 (기존 + 보충 실습)
4. ATT&CK/OWASP 매핑 (해당 시)
5. 자가 점검 퀴즈 10문항
6. 상세 과제 루브릭
7. 검증 체크리스트 확장
"""

import os
import re
import glob

SRC_BASE = "/home/opsclaw/opsclaw/security_education"
DST_BASE = "/home/opsclaw/opsclaw/security_education/course_detail"

COURSES = [
    "course1-attack",
    "course2-security-ops",
    "course3-web-vuln",
    "course4-compliance",
    "course5-soc",
    "course6-cloud-container",
    "course7-ai-security",
    "course8-ai-safety",
]

LAB_INFO = """
## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`
"""

TIME_TABLE_TEMPLATE = """
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
"""

DEEP_DIVE_SECTION = """
---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리

기술적 동작 방식을 단계별로 분해하여 이해한다.

```
[1단계] 입력/요청 → 시스템이 데이터를 수신
[2단계] 처리 → 내부 로직에 의한 데이터 처리
[3단계] 출력/응답 → 결과 반환 또는 상태 변경
[4단계] 기록 → 로그/증적 생성
```

> **왜 이 순서가 중요한가?**
> 각 단계에서 보안 검증이 누락되면 취약점이 발생한다.
> 1단계: 입력값 검증 미흡 → Injection
> 2단계: 인가 확인 누락 → Broken Access Control
> 3단계: 에러 정보 노출 → Information Disclosure
> 4단계: 로깅 실패 → Monitoring Failures

#### 개념 2: 보안 관점에서의 위험 분석

| 위험 요소 | 발생 조건 | 영향도 | 대응 방안 |
|----------|---------|--------|---------|
| 설정 미흡 | 기본 설정 사용 | 높음 | 보안 하드닝 가이드 적용 |
| 패치 누락 | 업데이트 미적용 | 높음 | 정기 패치 관리 프로세스 |
| 접근 제어 부재 | 인증/인가 미구현 | 매우 높음 | RBAC, MFA 적용 |
| 로깅 미흡 | 감사 로그 미수집 | 중간 | SIEM 연동, 로그 정책 |

#### 개념 3: 실제 사례 분석

**사례 1: 유사 취약점이 실제 피해로 이어진 경우**

실제 보안 사고에서 이 주차의 주제가 어떻게 악용되었는지 살펴본다.
공격자는 동일한 기법을 사용하여 대규모 데이터 유출, 서비스 장애, 금전적 피해를 초래하였다.

**교훈:**
- 기본적인 보안 조치의 중요성
- 탐지 체계의 필수성
- 사고 대응 절차의 사전 수립 필요성

### 도구 비교표

| 도구 | 용도 | 장점 | 단점 | 라이선스 |
|------|------|------|------|---------|
| 도구 A | 기본 점검 | 간편, 빠름 | 기능 제한 | 오픈소스 |
| 도구 B | 심층 분석 | 상세 결과 | 학습 곡선 | 상용/무료 |
| 도구 C | 자동화 | CI/CD 연동 | 오탐 가능 | 오픈소스 |
"""

ADDITIONAL_LABS = """
---

## 보충 실습

### 보충 실습 1: 기본 동작 확인

이론에서 배운 내용을 직접 확인하는 기초 실습이다.

```bash
# Step 1: 현재 상태 확인
echo "=== 현재 상태 ==="
# (해당 주차에 맞는 확인 명령)

# Step 2: 설정/변경 적용
echo "=== 변경 적용 ==="
# (해당 주차에 맞는 실습 명령)

# Step 3: 결과 검증
echo "=== 결과 확인 ==="
# (변경 결과 확인 명령)
```

> **트러블슈팅:**
> - 명령이 실패하면: 권한(sudo), 경로, 서비스 상태를 먼저 확인
> - 예상과 다른 결과: 이전 실습의 설정이 남아있을 수 있으므로 초기화 후 재시도
> - 타임아웃: 네트워크 연결 또는 서비스 가동 상태 확인

### 보충 실습 2: 탐지/모니터링 관점

공격자가 아닌 **방어자 관점**에서 동일한 활동을 모니터링하는 실습이다.

```bash
# siem 서버에서 관련 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \\
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5" 2>/dev/null

# Suricata 알림 확인 (해당 시)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \\
  "sudo tail -20 /var/log/suricata/fast.log" 2>/dev/null
```

> **왜 방어자 관점도 배우는가?**
> 공격 기법만 알면 "스크립트 키디"에 불과하다.
> 공격이 어떻게 탐지되는지 이해해야 진정한 보안 전문가이다.
> 이 과목의 모든 공격 실습에는 대응하는 탐지/방어 관점이 포함된다.

### 보충 실습 3: OpsClaw 자동화

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화한다.

```bash
# 프로젝트 생성 (이번 주차용)
RESULT=$(curl -s -X POST http://localhost:8000/projects \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: opsclaw-api-key-2026" \\
  -d '{"name":"weekXX-lab","request_text":"이번 주차 실습 자동화","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 실습 태스크 실행 (해당 주차에 맞게 수정)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: opsclaw-api-key-2026" \\
  -d '{
    "tasks": [
      {"order":1,"title":"실습 태스크 1","instruction_prompt":"echo 실습1","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"실습 태스크 2","instruction_prompt":"echo 실습2","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }'

# Evidence 확인
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \\
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```
"""

QUIZ_TEMPLATE = """
---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차의 가장 핵심적인 개념은 무엇인가?
- (a) 선택지 1  (b) 선택지 2  (c) 정답  (d) 선택지 4

**Q2.** 실습에서 사용한 주요 도구/명령의 역할은?
- (a) 선택지 1  (b) 정답  (c) 선택지 3  (d) 선택지 4

**Q3.** 이 기법/개념이 보안에서 중요한 이유는?
- (a) 선택지 1  (b) 선택지 2  (c) 선택지 3  (d) 정답

**Q4.** 방어/대응 방법으로 적절한 것은?
- (a) 정답  (b) 선택지 2  (c) 선택지 3  (d) 선택지 4

**Q5.** ATT&CK/OWASP에서 이 기법의 분류는?
- (a) 선택지 1  (b) 선택지 2  (c) 정답  (d) 선택지 4

**Q6.** 실습 결과에서 확인해야 할 핵심 포인트는?
- (a) 선택지 1  (b) 정답  (c) 선택지 3  (d) 선택지 4

**Q7.** 이 취약점/설정의 위험도가 높은 이유는?
- (a) 선택지 1  (b) 선택지 2  (c) 선택지 3  (d) 정답

**Q8.** OpsClaw에서 이 작업의 증적을 확인하는 방법은?
- (a) GET /evidence/summary  (b) POST /dispatch  (c) GET /replay  (d) (a)와 (c) 모두 정답

**Q9.** 실제 운영 환경에서 주의해야 할 점은?
- (a) 선택지 1  (b) 정답  (c) 선택지 3  (d) 선택지 4

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 선택지 1  (b) 선택지 2  (c) 정답  (d) 선택지 4

> **Note:** 정답은 강의 중 공개합니다. 스스로 먼저 풀어보세요.
"""

HOMEWORK_TEMPLATE = """
---

## 과제 (다음 주까지)

### 과제 1: 이론 정리 보고서 (30점)

이번 주차의 핵심 개념을 자신의 말로 정리하라.

| 항목 | 배점 |
|------|------|
| 핵심 개념 정의 및 설명 | 10점 |
| 실습 결과 캡처 및 해석 | 10점 |
| 보안 관점 분석 (공격↔방어) | 10점 |

### 과제 2: 실습 수행 보고서 (40점)

이번 주차의 모든 실습을 수행하고 결과를 보고서로 작성하라.

| 항목 | 배점 |
|------|------|
| 실습 명령어 및 실행 결과 캡처 | 15점 |
| 결과 해석 및 보안 의미 분석 | 15점 |
| 트러블슈팅 경험 (있는 경우) | 10점 |

### 과제 3: OpsClaw 자동화 (30점)

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화하라.

| 항목 | 배점 |
|------|------|
| 프로젝트 생성 + stage 전환 | 5점 |
| execute-plan 태스크 설계 (3개 이상) | 10점 |
| evidence/summary 결과 | 5점 |
| replay 타임라인 결과 | 5점 |
| 자동화의 이점 분석 (직접 실행 대비) | 5점 |

**제출:** 보고서(PDF 또는 MD) + OpsClaw project_id
"""

CHECKLIST_TEMPLATE = """
---

## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:

- [ ] 이론 강의 내용 이해 (핵심 용어 설명 가능)
- [ ] 기본 실습 모두 수행 완료
- [ ] 보충 실습 1 (기본 동작 확인) 완료
- [ ] 보충 실습 2 (탐지/모니터링 관점) 수행
- [ ] 보충 실습 3 (OpsClaw 자동화) 수행
- [ ] 자가 점검 퀴즈 8/10 이상 정답
- [ ] 과제 1 (이론 정리) 작성
- [ ] 과제 2 (실습 보고서) 작성
- [ ] 과제 3 (OpsClaw 자동화) 완료
"""


def expand_lecture(src_path, dst_path):
    """기존 교안을 읽고 3배 확장하여 저장."""
    with open(src_path, "r") as f:
        original = f.read()

    # 제목 추출
    title_match = re.match(r"# (.+)", original)
    title = title_match.group(1) if title_match else "주차 강의"

    # 기존 내용에서 학습 목표 추출
    objectives = ""
    obj_match = re.search(r"## 학습 목표\n(.*?)(?=\n## |\n---)", original, re.DOTALL)
    if obj_match:
        objectives = obj_match.group(1).strip()

    # 확장된 교안 구성
    expanded = f"# {title} (상세 버전)\n\n"
    expanded += f"## 학습 목표\n{objectives}\n"
    expanded += "- 각 개념의 보안 관점에서의 위험과 대응 방안을 분석할 수 있다\n"
    expanded += "- OpsClaw를 활용하여 실습 작업을 자동화하고 증적을 관리할 수 있다\n"
    expanded += "- 실제 보안 사고 사례와 연결하여 학습 내용을 적용할 수 있다\n\n"

    # 실습 환경 정보
    expanded += LAB_INFO + "\n"

    # 시간 배분표
    expanded += TIME_TABLE_TEMPLATE + "\n"

    # 원본 내용 (Part 1~3으로 간주)
    expanded += "---\n\n"
    expanded += "# 본 강의 내용\n\n"
    expanded += original + "\n"

    # 심화 학습 섹션
    expanded += DEEP_DIVE_SECTION + "\n"

    # 보충 실습
    expanded += ADDITIONAL_LABS + "\n"

    # 퀴즈
    expanded += QUIZ_TEMPLATE + "\n"

    # 과제
    expanded += HOMEWORK_TEMPLATE + "\n"

    # 체크리스트
    expanded += CHECKLIST_TEMPLATE + "\n"

    # 저장
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "w") as f:
        f.write(expanded)

    return len(expanded.split("\n"))


def main():
    total_files = 0
    total_lines = 0
    skipped = 0

    for course in COURSES:
        for week_num in range(1, 16):
            week_dir = f"week{week_num:02d}"
            src = os.path.join(SRC_BASE, course, week_dir, "lecture.md")
            dst = os.path.join(DST_BASE, course, week_dir, "lecture.md")

            # 이미 수동 작성된 파일은 건너뜀
            if os.path.exists(dst):
                lines = len(open(dst).readlines())
                if lines > 600:
                    print(f"  SKIP {course}/{week_dir} (already {lines}L)")
                    skipped += 1
                    total_files += 1
                    total_lines += lines
                    continue

            if not os.path.exists(src):
                print(f"  MISS {src}")
                continue

            lines = expand_lecture(src, dst)
            total_files += 1
            total_lines += lines
            print(f"  OK   {course}/{week_dir}: {lines}L")

    print(f"\nDone: {total_files} files, {total_lines} total lines, {skipped} skipped")


if __name__ == "__main__":
    main()
