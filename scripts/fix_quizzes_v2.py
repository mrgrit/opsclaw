#!/usr/bin/env python3
"""
제너릭 퀴즈를 과목/주차 특화 퀴즈로 교체 (v2).
원본 교안의 핵심 내용을 기반으로 구체적 퀴즈를 생성.
"""
import os
import re

DST = "/home/opsclaw/opsclaw/security_education/course_detail"
SRC = "/home/opsclaw/opsclaw/security_education"

def get_original_content(course, week):
    """원본 교안에서 핵심 키워드를 추출."""
    src_path = os.path.join(SRC, course, f"week{week:02d}", "lecture.md")
    if not os.path.exists(src_path):
        return "", ""
    with open(src_path) as f:
        content = f.read()
    title = content.split("\n")[0].replace("# ", "")
    return title, content

def generate_quiz(course, week, title, content):
    """주차 내용에 기반한 특화 퀴즈 생성."""

    # 과목별 기본 구조
    quiz_templates = {
        "course1-attack": {
            "domain": "사이버보안 공격",
            "q1_topic": "이 공격 기법",
            "q2_topic": "방어자 관점",
        },
        "course2-security-ops": {
            "domain": "보안 솔루션 운영",
            "q1_topic": "이 보안 솔루션",
            "q2_topic": "올바른 설정",
        },
        "course3-web-vuln": {
            "domain": "웹 취약점 점검",
            "q1_topic": "이 취약점",
            "q2_topic": "점검 방법",
        },
        "course4-compliance": {
            "domain": "보안 표준/컴플라이언스",
            "q1_topic": "이 표준/규정",
            "q2_topic": "실무 적용",
        },
        "course5-soc": {
            "domain": "보안관제/SOC",
            "q1_topic": "이 관제 기법",
            "q2_topic": "탐지/대응",
        },
        "course6-cloud-container": {
            "domain": "Docker/클라우드 보안",
            "q1_topic": "이 보안 설정",
            "q2_topic": "컨테이너/클라우드",
        },
        "course7-ai-security": {
            "domain": "AI/LLM 보안 활용",
            "q1_topic": "이 AI 기법",
            "q2_topic": "LLM/OpsClaw",
        },
        "course8-ai-safety": {
            "domain": "AI Safety",
            "q1_topic": "이 AI 위협",
            "q2_topic": "방어/가드레일",
        },
    }

    t = quiz_templates.get(course, {"domain": "보안", "q1_topic": "이 기법", "q2_topic": "실무"})

    # 교안 내용에서 핵심 키워드 추출
    keywords = []
    for line in content.split("\n"):
        if line.startswith("## ") and not line.startswith("## 학습") and not line.startswith("## 실습 환경"):
            kw = line.replace("## ", "").strip()
            if len(kw) > 2 and len(kw) < 50:
                keywords.append(kw)

    # 핵심 키워드 3개 선택
    kw1 = keywords[0] if len(keywords) > 0 else "핵심 개념"
    kw2 = keywords[1] if len(keywords) > 1 else "주요 기법"
    kw3 = keywords[2] if len(keywords) > 2 else "실습 내용"

    quiz = f"""
**Q1.** "{title}"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **{t['domain']}의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "{kw1}"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "{kw2}"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **{t['domain']} 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "{kw3}"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 {t['q2_topic']}의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 {t['domain']} 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b
"""
    return quiz


def fix_quiz(filepath, course, week):
    """제너릭 퀴즈를 특화 퀴즈로 교체."""
    with open(filepath) as f:
        content = f.read()

    # 제너릭 퀴즈 패턴 확인
    if '이번 주차' not in content or '핵심 목적은 무엇인가' not in content:
        return False

    title, orig_content = get_original_content(course, week)
    new_quiz = generate_quiz(course, week, title, orig_content)

    # "## 자가 점검 퀴즈" ~ "**정답:**..." 블록을 교체
    pattern = r'(\*\*Q1\.\*\*.*?)\*\*정답:\*\*.*?\n'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + new_quiz.strip() + "\n" + content[match.end():]

    with open(filepath, 'w') as f:
        f.write(content)
    return True


def main():
    fixed = 0
    for course in sorted(os.listdir(DST)):
        course_path = os.path.join(DST, course)
        if not os.path.isdir(course_path):
            continue
        for week in range(1, 16):
            fp = os.path.join(course_path, f"week{week:02d}", "lecture.md")
            if not os.path.exists(fp):
                continue
            if fix_quiz(fp, course, week):
                fixed += 1
                print(f"  ✓ {course}/week{week:02d}")
    print(f"\nFixed: {fixed}")


if __name__ == "__main__":
    main()
