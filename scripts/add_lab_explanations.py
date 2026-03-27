#!/usr/bin/env python3
"""
각 교안의 첫 번째 실습 섹션에 "왜 하는가" 설명을 자동 추가.
이미 설명이 있는 파일은 건너뜀.
"""
import os
import re

DST = "/home/opsclaw/opsclaw/security_education/course_detail"
SRC = "/home/opsclaw/opsclaw/security_education"

# 과목별 설명 템플릿
COURSE_CONTEXT = {
    "course1-attack": ("사이버보안 공격/웹해킹/침투테스트", "모의해킹 보고서에서 이 기법의 발견은 위험도 분류의 핵심 근거가 된다."),
    "course2-security-ops": ("보안 솔루션 운영", "보안 엔지니어가 인프라를 구축/운영할 때 이 솔루션의 설정과 관리가 핵심 업무이다."),
    "course3-web-vuln": ("웹 취약점 점검", "취약점 점검 보고서에서 이 발견사항은 고객사에게 구체적인 대응 방안과 함께 전달된다."),
    "course4-compliance": ("보안 표준/컴플라이언스", "인증 심사에서 이 통제 항목의 이행 여부가 적합/부적합 판정의 근거가 된다."),
    "course5-soc": ("보안관제/SOC", "SOC 분석가의 일상 업무에서 이 기법은 경보 분석과 인시던트 대응의 핵심이다."),
    "course6-cloud-container": ("Docker/클라우드/K8s 보안", "클라우드 환경에서 이 보안 설정은 컨테이너 탈출, 데이터 유출 등을 방지하는 핵심 방어선이다."),
    "course7-ai-security": ("AI/LLM 보안 활용", "AI 보안 자동화에서 이 기법은 로그 분석, 룰 생성, 대응 실행을 LLM이 수행하는 기반이다."),
    "course8-ai-safety": ("AI Safety", "AI 시스템의 안전성 평가에서 이 위협/방어 기법은 Red Teaming의 핵심 테스트 항목이다."),
}

def get_title_and_first_section(filepath):
    """교안 제목과 첫 번째 실습 섹션의 위치를 반환."""
    with open(filepath) as f:
        content = f.read()

    # 제목 추출 (# Week XX: ...)
    title_match = re.search(r'^# (Week \d+: .+)', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "이번 주차"

    # 첫 번째 "## N. " 실습 섹션 찾기 (원본 교안 섹션)
    # "## 1." 또는 "## 2." 등 (용어 해설/시간 배분 이후의 본문)
    sections = list(re.finditer(r'^## \d+\. ', content, re.MULTILINE))

    return title, content, sections

def add_explanation(filepath, course):
    """첫 번째 실습 섹션에 설명을 추가."""
    with open(filepath) as f:
        content = f.read()

    # 이미 설명이 있으면 건너뜀
    if '이 실습을 왜 하는가' in content or '이걸 하면 무엇을 알' in content:
        return False

    title, content, sections = get_title_and_first_section(filepath)
    if not sections:
        return False

    course_desc, practical_note = COURSE_CONTEXT.get(course, ("보안", "실무에서 이 기법은 핵심 업무의 일부이다."))

    # 원본 교안의 첫 번째 실습 관련 섹션 (## 2. 또는 ## 3. 쯤)
    # 보통 ## 1.은 이론, ## 2.부터 실습인 경우가 많음
    target_section = sections[1] if len(sections) > 1 else sections[0]

    # 해당 섹션 제목 추출
    section_end = content.find('\n', target_section.start())
    section_title = content[target_section.start():section_end].strip()

    explanation = f"""
> **이 실습을 왜 하는가?**
> {course_desc} 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> {practical_note}
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

"""

    # 섹션 제목 바로 다음 줄에 삽입
    insert_pos = section_end + 1
    content = content[:insert_pos] + explanation + content[insert_pos:]

    with open(filepath, 'w') as f:
        f.write(content)
    return True


def main():
    added = 0
    for course in sorted(os.listdir(DST)):
        course_path = os.path.join(DST, course)
        if not os.path.isdir(course_path):
            continue
        for week in range(1, 16):
            fp = os.path.join(course_path, f"week{week:02d}", "lecture.md")
            if not os.path.exists(fp):
                continue
            if add_explanation(fp, course):
                added += 1
                print(f"  ✓ {course}/week{week:02d}")
    print(f"\nAdded: {added}")


if __name__ == "__main__":
    main()
