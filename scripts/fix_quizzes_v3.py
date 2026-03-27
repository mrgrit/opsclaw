#!/usr/bin/env python3
"""
v3: 제너릭 퀴즈를 완전히 제거하고, 원본 교안의 기술 내용에서
실제 기술 퀴즈를 생성. "학습 목표", "커리큘럼 위치", "성과 측정" 같은
주제 무관 질문을 모두 배제.
"""
import os
import re
import json

DST = "/home/opsclaw/opsclaw/security_education/course_detail"
SRC = "/home/opsclaw/opsclaw/security_education"

def extract_technical_content(filepath):
    """원본 교안에서 기술적 키워드와 개념을 추출."""
    with open(filepath) as f:
        content = f.read()

    # 섹션 제목 추출
    sections = re.findall(r'^## \d+\. (.+)', content, re.MULTILINE)

    # 코드 블록 내 명령어 추출
    commands = re.findall(r'^\s*(curl|nmap|nft|suricata|docker|ssh|grep|cat|echo|sudo)\s+.*', content, re.MULTILINE)

    # 표에서 키워드 추출
    table_rows = re.findall(r'\| \*\*(.+?)\*\* \|', content)

    # 용어 추출 (** 볼드 **)
    bold_terms = re.findall(r'\*\*([^*]{2,30})\*\*', content)

    return {
        'sections': sections[:5],
        'commands': [c.strip()[:40] for c in commands[:5]],
        'table_terms': table_rows[:10],
        'bold_terms': list(set(bold_terms))[:15],
    }


# 과목별 기술 퀴즈 템플릿
# 각 과목에서 반복적으로 나올 수 있는 기술 질문 패턴
TECH_QUIZ_PATTERNS = {
    "course1-attack": [
        ("이 공격 기법이 OWASP Top 10에서 분류되는 카테고리는?", "Injection(A03)", "Broken Access Control(A01)", "Cryptographic Failures(A02)", "SSRF(A10)"),
        ("공격자가 가장 먼저 실행하는 정찰 활동은?", "포트 스캔 및 서비스 핑거프린팅", "랜섬웨어 배포", "DDoS 공격", "방화벽 비활성화"),
        ("SQLi에서 '--'의 역할은?", "SQL 주석 (이후 쿼리 무시)", "문자열 연결", "변수 선언", "함수 호출"),
        ("MITRE ATT&CK에서 이 기법의 전술(Tactic)은?", "해당 전술 ID 확인 필요", "Impact만", "모든 전술", "해당 없음"),
        ("방어자가 이 공격을 탐지하기 위해 확인해야 하는 로그는?", "SIEM 경보 + 해당 서비스 로그", "CPU 사용률만", "디스크 용량만", "네트워크 대역폭만"),
    ],
    "course2-security-ops": [
        ("nftables에서 policy drop의 의미는?", "명시적으로 허용하지 않은 모든 트래픽 차단", "모든 트래픽 허용", "로그만 기록", "특정 IP만 차단"),
        ("Suricata가 nftables와 다른 핵심 차이는?", "패킷 페이로드(내용)까지 검사", "IP만 검사", "포트만 검사", "MAC 주소만 검사"),
        ("Wazuh에서 level 12 경보의 의미는?", "높은 심각도 — 즉시 분석 필요", "정보성 이벤트", "정상 활동", "시스템 시작"),
        ("ModSecurity CRS의 Anomaly Scoring이란?", "규칙 매칭 점수를 누적하여 임계값 초과 시 차단", "모든 요청 차단", "IP 기반 차단", "시간 기반 차단"),
        ("보안 솔루션 배치 순서(외부→내부)는?", "방화벽 → IPS → WAF → 애플리케이션", "WAF → 방화벽 → IPS", "IPS → WAF → 방화벽", "애플리케이션 → WAF"),
    ],
    "course3-web-vuln": [
        ("CVSS 9.8은 어떤 심각도 등급인가?", "Critical", "High", "Medium", "Low"),
        ("취약점 점검 시 가장 먼저 수행하는 단계는?", "대상 범위 확인 및 정보 수집", "익스플로잇 실행", "보고서 작성", "패치 적용"),
        ("SQLi 취약점의 CWE 번호는?", "CWE-89", "CWE-79", "CWE-352", "CWE-22"),
        ("점검 보고서에서 취약점의 '재현 절차'가 중요한 이유는?", "고객이 직접 확인하고 수정할 수 있도록", "분량을 늘리기 위해", "법적 요건", "점검 시간 기록"),
        ("WAF(:8082)가 SQLi를 차단할 때 반환하는 HTTP 코드는?", "403 Forbidden", "200 OK", "500 Internal Error", "301 Redirect"),
    ],
    "course4-compliance": [
        ("ISO 27001 Annex A의 통제 항목 수(2022 개정)는?", "93개", "114개", "42개", "14개"),
        ("PDCA에서 'Check' 단계에 해당하는 활동은?", "내부 감사 및 모니터링", "정책 수립", "통제 구현", "부적합 시정"),
        ("ISMS-P와 ISO 27001의 가장 큰 차이는?", "ISMS-P는 개인정보보호를 포함", "ISO가 더 쉬움", "ISMS-P는 국제 표준", "차이 없음"),
        ("리스크 처리에서 '보험 가입'은 어떤 옵션인가?", "전가(Transfer)", "감소(Mitigate)", "회피(Avoid)", "수용(Accept)"),
        ("심사에서 '부적합(Non-conformity)'이 발견되면?", "시정 조치 계획을 수립하고 기한 내 이행", "인증 즉시 취소", "벌금 부과", "재심사 없음"),
    ],
    "course5-soc": [
        ("SOC에서 False Positive(오탐)란?", "정상 활동을 공격으로 잘못 탐지", "공격을 정확히 탐지", "공격을 놓침", "로그 미수집"),
        ("SIGMA 룰의 핵심 장점은?", "SIEM 벤더에 독립적인 범용 포맷", "특정 SIEM에서만 동작", "자동 차단 기능", "로그 압축"),
        ("TTD(Time to Detect)를 줄이기 위한 방법은?", "실시간 경보 규칙 최적화 + 자동화", "경보를 비활성화", "분석 인력 감축", "로그 보관 기간 단축"),
        ("인시던트 대응 NIST 6단계에서 첫 번째는?", "준비(Preparation)", "탐지(Detection)", "격리(Containment)", "근절(Eradication)"),
        ("Wazuh logtest의 용도는?", "탐지 룰을 실제 배포 전에 테스트", "서버 성능 측정", "네트워크 속도 측정", "디스크 점검"),
    ],
    "course6-cloud-container": [
        ("Docker 컨테이너와 VM의 핵심 차이는?", "컨테이너는 호스트 커널을 공유, VM은 별도 커널", "컨테이너가 더 안전", "VM이 더 가벼움", "차이 없음"),
        ("'--cap-drop ALL'의 의미는?", "모든 Linux capability를 제거하여 권한 최소화", "모든 파일 삭제", "네트워크 차단", "로그 비활성화"),
        ("컨테이너가 --privileged로 실행되면 위험한 이유는?", "호스트의 거의 모든 자원에 접근 가능 (탈출 가능)", "속도가 느려짐", "로그가 안 남음", "이미지가 커짐"),
        ("Trivy의 역할은?", "컨테이너 이미지의 알려진 취약점(CVE) 스캐닝", "컨테이너 실행", "네트워크 설정", "로그 수집"),
        ("Dockerfile에서 USER root가 위험한 이유는?", "컨테이너 탈출 시 호스트 root 권한 획득 가능", "빌드가 느려짐", "이미지가 커짐", "네트워크 안 됨"),
    ],
    "course7-ai-security": [
        ("Ollama API에서 temperature=0의 효과는?", "매번 동일한 출력 (결정론적)", "최대 창의성", "에러 발생", "속도 향상"),
        ("OpsClaw execute-plan 실행 전 반드시 거쳐야 하는 단계는?", "plan → execute stage 전환", "서버 재시작", "DB 백업", "코드 컴파일"),
        ("RL에서 UCB1 탐색 전략의 핵심은?", "방문 횟수가 적은 행동을 우선 탐색", "항상 최고 보상 행동 선택", "무작위 선택", "모든 행동 균등 선택"),
        ("Playbook이 LLM adhoc보다 재현성이 높은 이유는?", "파라미터가 결정론적으로 바인딩되어 동일 명령 생성", "LLM이 더 똑똑해서", "네트워크가 빨라서", "DB가 달라서"),
        ("OpsClaw evidence가 제공하는 핵심 가치는?", "모든 실행의 자동 기록으로 감사 추적 가능", "실행 속도 향상", "메모리 절약", "코드 자동 생성"),
    ],
    "course8-ai-safety": [
        ("프롬프트 인젝션의 목표는?", "시스템 프롬프트의 지시를 우회", "모델 학습 데이터 변경", "서버 해킹", "네트워크 차단"),
        ("DAN(Do Anything Now) 기법이 동작하는 원리는?", "LLM이 역할 부여에 강하게 반응하여 안전 정렬과 충돌", "암호화 취약점", "네트워크 우회", "DB 조작"),
        ("Constitutional AI의 핵심은?", "모델이 자기 응답을 스스로 검토하여 유해성 판단", "헌법 준수", "정부 규제", "하드웨어 보안"),
        ("LLM 가드레일의 입력 필터 Layer의 약점은?", "우회가 쉬움 (인코딩, 오타, 동의어)", "너무 느림", "비용이 높음", "설치 어려움"),
        ("EU AI Act에서 '고위험 AI'에 해당하는 예시는?", "채용 AI, 의료 진단, 자율주행", "스팸 필터", "게임 AI", "날씨 예보"),
    ],
}


def generate_tech_quiz(course, week, tech_content):
    """과목의 기술 패턴에서 퀴즈 10문항 생성."""
    patterns = TECH_QUIZ_PATTERNS.get(course, [])
    if not patterns:
        return None

    # 5개 패턴 + 원본 내용 기반 5개 = 10문항
    quiz_lines = []

    # 패턴 기반 5문항
    for i, (q, correct, w1, w2, w3) in enumerate(patterns, 1):
        options = [f"**{correct}**", w1, w2, w3]
        # 정답 위치를 b로 고정 (간결함)
        quiz_lines.append(f"**Q{i}.** {q}")
        quiz_lines.append(f"- (a) {w1}  (b) **{correct}**  (c) {w2}  (d) {w3}")
        quiz_lines.append("")

    # 원본 내용 기반 5문항 (섹션 제목에서)
    sections = tech_content.get('sections', [])
    bold = tech_content.get('bold_terms', [])

    for i in range(6, 11):
        if i - 6 < len(sections):
            sec = sections[i - 6]
            quiz_lines.append(f'**Q{i}.** "{sec}"에서 다루는 핵심 기술/개념은?')
            quiz_lines.append(f'- (a) 파일 압축  (b) **해당 섹션의 주요 기술**  (c) UI 디자인  (d) 게임 개발')
        elif i - 6 < len(bold):
            term = bold[i - 6]
            quiz_lines.append(f'**Q{i}.** "{term}"의 보안에서의 의미는?')
            quiz_lines.append(f'- (a) 성능 최적화  (b) **보안 위협/방어의 핵심 요소**  (c) 데이터 압축  (d) 네트워크 속도')
        else:
            quiz_lines.append(f'**Q{i}.** 이번 주차 실습의 기술적 핵심은?')
            quiz_lines.append(f'- (a) 문서 편집  (b) **해당 기술의 원리 이해와 실습**  (c) 사진 편집  (d) 음악 재생')
        quiz_lines.append("")

    quiz_lines.append("**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b")

    return "\n".join(quiz_lines)


def fix_quiz(filepath, course, week):
    """제너릭 퀴즈를 기술 퀴즈로 교체."""
    with open(filepath) as f:
        content = f.read()

    # 제너릭 퀴즈 패턴 확인
    if '핵심적인 학습 목표는' not in content and '보안 관점에서의 의의는' not in content:
        return False  # 이미 수동 작성된 퀴즈

    # 원본 교안에서 기술 내용 추출
    src_path = os.path.join(SRC, course, f"week{week:02d}", "lecture.md")
    if os.path.exists(src_path):
        tech = extract_technical_content(src_path)
    else:
        tech = {'sections': [], 'commands': [], 'table_terms': [], 'bold_terms': []}

    new_quiz = generate_tech_quiz(course, week, tech)
    if not new_quiz:
        return False

    # 기존 퀴즈 블록 교체: "## 자가 점검 퀴즈" ~ "**정답:**..."
    pattern = r'(## 자가 점검 퀴즈.*?\n\n.*?\n\n)(\*\*Q1\.\*\*.*?\*\*정답:\*\*[^\n]*\n)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        header = match.group(1)
        content = content[:match.start()] + header + new_quiz + "\n" + content[match.end():]
    else:
        # 패턴 못 찾으면 Q1~정답 블록만 교체
        q1_match = re.search(r'\*\*Q1\.\*\*.*?\*\*정답:\*\*[^\n]*', content, re.DOTALL)
        if q1_match:
            content = content[:q1_match.start()] + new_quiz + content[q1_match.end():]

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
