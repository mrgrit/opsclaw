#!/usr/bin/env python3
"""
제너릭 실습 설명을 과목/주차 특화 설명으로 교체.
"""
import os
import re

DST = "/home/opsclaw/opsclaw/security_education/course_detail"
SRC = "/home/opsclaw/opsclaw/security_education"

GENERIC = """> **이 실습을 왜 하는가?**
> {domain} 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> {practical}
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다."""

COURSE_PRACTICAL = {
    "course1-attack": "모의해킹 보고서에서 이 기법의 발견은 위험도 분류의 핵심 근거가 된다.",
    "course2-security-ops": "보안 엔지니어가 인프라를 구축/운영할 때 이 솔루션의 설정과 관리가 핵심 업무이다.",
    "course3-web-vuln": "취약점 점검 보고서에서 이 발견사항은 고객사에게 구체적인 대응 방안과 함께 전달된다.",
    "course4-compliance": "인증 심사에서 이 통제 항목의 이행 여부가 적합/부적합 판정의 근거가 된다.",
    "course5-soc": "SOC 분석가의 일상 업무에서 이 기법은 경보 분석과 인시던트 대응의 핵심이다.",
    "course6-cloud-container": "클라우드 환경에서 이 보안 설정은 컨테이너 탈출, 데이터 유출 등을 방지하는 핵심 방어선이다.",
    "course7-ai-security": "AI 보안 자동화에서 이 기법은 로그 분석, 룰 생성, 대응 실행을 LLM이 수행하는 기반이다.",
    "course8-ai-safety": "AI 시스템의 안전성 평가에서 이 위협/방어 기법은 Red Teaming의 핵심 테스트 항목이다.",
}

COURSE_DOMAIN = {
    "course1-attack": "사이버보안 공격/웹해킹/침투테스트",
    "course2-security-ops": "보안 솔루션 운영",
    "course3-web-vuln": "웹 취약점 점검",
    "course4-compliance": "보안 표준/컴플라이언스",
    "course5-soc": "보안관제/SOC",
    "course6-cloud-container": "Docker/클라우드/K8s 보안",
    "course7-ai-security": "AI/LLM 보안 활용",
    "course8-ai-safety": "AI Safety",
}

# 과목별 주차별 특화 설명
SPECIFIC_EXPLANATIONS = {}

def get_week_title(course, week):
    src = os.path.join(SRC, course, f"week{week:02d}", "lecture.md")
    if os.path.exists(src):
        with open(src) as f:
            return f.readline().strip().replace("# ", "")
    return ""

def generate_specific(course, week, title):
    """주차 제목에서 특화 설명 생성."""
    domain = COURSE_DOMAIN.get(course, "보안")

    # 주차 제목에서 핵심 키워드 추출
    keywords = title.replace(f"Week {week:02d}: ", "").strip()

    return f"""> **이 실습을 왜 하는가?**
> "{keywords}" — 이 주차의 핵심 기술을 실제 서버 환경에서 직접 실행하여 체험한다.
> {domain} 분야에서 이 기술은 실무의 핵심이며, 실습을 통해
> 명령어의 의미, 결과 해석 방법, 보안 관점에서의 판단 기준을 익힌다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이 기술이 실제 시스템에서 어떻게 동작하는지 직접 확인
> - 정상과 비정상 결과를 구분하는 눈을 기름
> - 실무에서 바로 활용할 수 있는 명령어와 절차를 체득
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다."""


def fix_file(filepath, course, week):
    with open(filepath) as f:
        content = f.read()

    # 제너릭 패턴 확인
    if "이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인" not in content:
        return False

    title = get_week_title(course, week)
    new_explanation = generate_specific(course, week, title)

    # 제너릭 블록 교체
    domain = COURSE_DOMAIN.get(course, "보안")
    practical = COURSE_PRACTICAL.get(course, "")
    generic_text = GENERIC.format(domain=domain, practical=practical)

    if generic_text in content:
        content = content.replace(generic_text, new_explanation)
    else:
        # 정확한 매칭이 안 되면, 핵심 패턴으로 교체
        pattern = r'> \*\*이 실습을 왜 하는가\?\*\*\n> .+?과목에서.*?10\.20\.30\.0/24\)에서만 수행한다\.'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = content[:match.start()] + new_explanation + content[match.end():]

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
            if fix_file(fp, course, week):
                fixed += 1
                print(f"  ✓ {course}/week{week:02d}")
    print(f"\nFixed: {fixed}")


if __name__ == "__main__":
    main()
