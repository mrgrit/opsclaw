#!/usr/bin/env python3
"""
교안 정리 스크립트:
1. 제너릭 템플릿 섹션 전체 제거 (심화 학습, 보충 실습, 제너릭 과제)
2. 용어 해설과 실제 퀴즈는 유지
3. 과목 특화 심화 내용은 유지
4. 시간 배분표는 유지
"""
import os
import re

DST = "/home/opsclaw/opsclaw/security_education/course_detail"

# 제거할 제너릭 블록의 시작 마커들
GENERIC_MARKERS = [
    "## 심화 학습: 개념 확장",
    "### 핵심 개념 상세 해설",
    "#### 개념 1: 동작 원리",
    "#### 개념 2: 보안 관점에서의 위험 분석",
    "#### 개념 3: 실제 사례 분석",
    "### 도구 비교표",
    "## 보충 실습",
    "### 보충 실습 1: 기본 동작 확인",
    "### 보충 실습 2: 탐지/모니터링 관점",
    "### 보충 실습 3: OpsClaw 자동화",
]

# 제거할 제너릭 텍스트 패턴
GENERIC_TEXTS = [
    "이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.",
    "기술적 동작 방식을 단계별로 분해하여 이해한다.",
    "이론에서 배운 내용을 직접 확인하는 기초 실습이다.",
    "공격자가 아닌 **방어자 관점**에서 동일한 활동을 모니터링하는 실습이다.",
    "이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화한다.",
    "# (해당 주차에 맞는 확인 명령)",
    "# (해당 주차에 맞는 실습 명령)",
    "# (변경 결과 확인 명령)",
    "# (해당 주차에 맞게 수정)",
    '{"order":1,"title":"실습 태스크 1","instruction_prompt":"echo 실습1"',
    '{"order":2,"title":"실습 태스크 2","instruction_prompt":"echo 실습2"',
    "| 도구 A | 기본 점검 | 간편, 빠름 | 기능 제한 | 오픈소스 |",
    "| 도구 B | 심층 분석 | 상세 결과 | 학습 곡선 | 상용/무료 |",
    "| 도구 C | 자동화 | CI/CD 연동 | 오탐 가능 | 오픈소스 |",
    "| 설정 미흡 | 기본 설정 사용 | 높음 | 보안 하드닝 가이드 적용 |",
    "| 패치 누락 | 업데이트 미적용 | 높음 | 정기 패치 관리 프로세스 |",
    "| 접근 제어 부재 | 인증/인가 미구현 | 매우 높음 | RBAC, MFA 적용 |",
    "| 로깅 미흡 | 감사 로그 미수집 | 중간 | SIEM 연동, 로그 정책 |",
    "**사례 1: 유사 취약점이 실제 피해로 이어진 경우**",
    "실제 보안 사고에서 이 주차의 주제가 어떻게 악용되었는지 살펴본다.",
    "공격자는 동일한 기법을 사용하여 대규모 데이터 유출, 서비스 장애, 금전적 피해를 초래하였다.",
]

# 제거할 제너릭 과제 섹션 (과목 특화가 아닌 것)
GENERIC_HOMEWORK_MARKERS = [
    "### 과제 1: 이론 정리 보고서 (30점)",
    "### 과제 2: 실습 수행 보고서 (40점)",
    "### 과제 3: OpsClaw 자동화 (30점)",
]

# 제거할 체크리스트 (제너릭)
GENERIC_CHECKLIST = [
    "- [ ] 이론 강의 내용 이해 (핵심 용어 설명 가능)",
    "- [ ] 기본 실습 모두 수행 완료",
    "- [ ] 보충 실습 1 (기본 동작 확인) 완료",
    "- [ ] 보충 실습 2 (탐지/모니터링 관점) 수행",
    "- [ ] 보충 실습 3 (OpsClaw 자동화) 수행",
    "- [ ] 자가 점검 퀴즈 8/10 이상 정답",
    "- [ ] 과제 1 (이론 정리) 작성",
    "- [ ] 과제 2 (실습 보고서) 작성",
    "- [ ] 과제 3 (OpsClaw 자동화) 완료",
]


def clean_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    original_len = len(content.split("\n"))
    changed = False

    # 1. 제너릭 블록 제거: "## 심화 학습: 개념 확장" ~ "## 보충 실습" 전체
    # 이 블록은 "## 심화 학습: 개념 확장"으로 시작하여 다음 "## 심화:" 또는 "## 자가" 까지
    pattern = r"\n## 심화 학습: 개념 확장\n.*?(?=\n## 심화:|\n## 자가 점검|\n---\n\n## 자가|\n---\n\n## 과제|\Z)"
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, "\n", content, flags=re.DOTALL)
        changed = True

    # 2. 제너릭 보충 실습 블록 제거
    pattern2 = r"\n## 보충 실습\n.*?(?=\n## 심화:|\n## 자가 점검|\n---\n\n## 자가|\n---\n\n## 과제|\Z)"
    if re.search(pattern2, content, re.DOTALL):
        content = re.sub(pattern2, "\n", content, flags=re.DOTALL)
        changed = True

    # 3. 개별 제너릭 텍스트 라인 제거
    for text in GENERIC_TEXTS:
        if text in content:
            content = content.replace(text, "")
            changed = True

    # 4. 제너릭 과제 블록 제거 (원본 교안에 이미 과제가 있는 경우)
    # "### 과제 1: 이론 정리 보고서" 로 시작하는 제너릭 과제 섹션
    for marker in GENERIC_HOMEWORK_MARKERS:
        if marker in content:
            # 이 과제 블록 전체를 찾아서 제거
            idx = content.find(marker)
            # 다음 "### 과제" 또는 "## " 찾기
            next_hw = content.find("\n### 과제", idx + len(marker))
            next_section = content.find("\n## ", idx + len(marker))
            end = min(x for x in [next_hw, next_section, len(content)] if x > 0)
            content = content[:idx] + content[end:]
            changed = True

    # 5. 제너릭 체크리스트 제거
    for item in GENERIC_CHECKLIST:
        content = content.replace(item + "\n", "")

    # 6. 연속 빈 줄 3개 이상을 2개로 줄이기
    content = re.sub(r"\n{4,}", "\n\n\n", content)

    # 7. "# 본 강의 내용" 마커 제거 (중복 제목 방지)
    content = content.replace("\n# 본 강의 내용\n", "\n---\n")

    if changed:
        with open(filepath, "w") as f:
            f.write(content)

    new_len = len(content.split("\n"))
    return original_len, new_len, changed


def main():
    cleaned = 0
    total_removed = 0

    for course in sorted(os.listdir(DST)):
        course_path = os.path.join(DST, course)
        if not os.path.isdir(course_path):
            continue

        for week in range(1, 16):
            fp = os.path.join(course_path, f"week{week:02d}", "lecture.md")
            if not os.path.exists(fp):
                continue

            old, new, changed = clean_file(fp)
            if changed:
                cleaned += 1
                removed = old - new
                total_removed += removed
                if removed > 20:
                    print(f"  ✓ {course}/week{week:02d}: {old}→{new} (-{removed}줄)")

    print(f"\nCleaned: {cleaned} files, removed {total_removed} generic lines")


if __name__ == "__main__":
    main()
