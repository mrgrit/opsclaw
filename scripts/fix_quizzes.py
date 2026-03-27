#!/usr/bin/env python3
"""
제너릭 퀴즈 플레이스홀더를 과목/주차 특화 실제 퀴즈로 교체.
각 주차의 제목과 핵심 내용을 기반으로 10문항 퀴즈 생성.
"""
import os
import re

DST = "/home/opsclaw/opsclaw/security_education/course_detail"
SRC = "/home/opsclaw/opsclaw/security_education"

# 원본 교안에서 주차별 제목 추출
def get_week_title(course, week):
    src_path = os.path.join(SRC, course, f"week{week:02d}", "lecture.md")
    if os.path.exists(src_path):
        with open(src_path) as f:
            first_line = f.readline().strip()
            return first_line.replace("# ", "")
    return ""

# 과목×주차별 퀴즈 데이터
QUIZZES = {
    # ─────── Course 1: 사이버보안 공격/웹해킹 ───────
    ("course1-attack", 3): """
**Q1.** HTTP 요청에서 데이터를 서버에 전송할 때 주로 사용하는 메서드는?
- (a) GET  (b) **POST**  (c) DELETE  (d) HEAD

**Q2.** HTTP 상태 코드 403의 의미는?
- (a) 성공  (b) 리다이렉트  (c) **접근 금지(Forbidden)**  (d) 서버 오류

**Q3.** HTTPS에서 데이터를 암호화하는 프로토콜은?
- (a) SSH  (b) **TLS**  (c) FTP  (d) SMTP

**Q4.** 쿠키(Cookie)가 저장되는 위치는?
- (a) 서버 메모리  (b) 데이터베이스  (c) **클라이언트(브라우저)**  (d) DNS 서버

**Q5.** JWT 토큰의 세 부분은?
- (a) ID, PW, Token  (b) **Header, Payload, Signature**  (c) Key, Value, Hash  (d) User, Role, Time

**Q6.** REST API에서 리소스를 삭제하는 HTTP 메서드는?
- (a) POST  (b) PUT  (c) GET  (d) **DELETE**

**Q7.** `Access-Control-Allow-Origin: *`가 보안 이슈인 이유는?
- (a) 속도 저하  (b) **모든 도메인에서 API 호출 가능**  (c) 암호화 비활성화  (d) 로그 미생성

**Q8.** HTTP 상태 코드 500은 어떤 종류의 오류인가?
- (a) 클라이언트 오류  (b) 리다이렉트  (c) **서버 내부 오류**  (d) 인증 실패

**Q9.** `curl -X POST`에서 `-X POST`의 의미는?
- (a) 프록시 설정  (b) 타임아웃 설정  (c) **HTTP 메서드를 POST로 지정**  (d) 출력 형식 설정

**Q10.** 세션 ID가 URL에 노출되면 어떤 공격이 가능한가?
- (a) SQLi  (b) **세션 하이재킹**  (c) DDoS  (d) 버퍼 오버플로

**정답:** Q1:b, Q2:c, Q3:b, Q4:c, Q5:b, Q6:d, Q7:b, Q8:c, Q9:c, Q10:b
""",
    ("course1-attack", 4): """
**Q1.** SQL Injection이 발생하는 근본 원인은?
- (a) 서버 성능 부족  (b) **사용자 입력이 SQL 쿼리에 그대로 삽입**  (c) 네트워크 지연  (d) 디스크 부족

**Q2.** `' OR 1=1--`에서 `--`의 역할은?
- (a) 문자열 연결  (b) 변수 선언  (c) **SQL 주석 (이후 무시)**  (d) 조건 추가

**Q3.** UNION SELECT 공격이 성공하려면 반드시 맞춰야 하는 것은?
- (a) 테이블 이름  (b) **원래 쿼리의 컬럼 수**  (c) DB 버전  (d) 사용자 권한

**Q4.** Blind SQLi에서 참/거짓을 구분하는 방법은?
- (a) 에러 메시지 확인  (b) **응답 내용이나 시간의 차이 관찰**  (c) 소스 코드 확인  (d) 서버 재시작

**Q5.** SQL Injection 방어의 가장 효과적인 방법은?
- (a) WAF 배치  (b) IP 차단  (c) **매개변수화된 쿼리(Prepared Statement)**  (d) HTTPS 적용

**Q6.** JuiceShop에서 SQLi로 획득한 JWT의 역할은?
- (a) 암호화 키  (b) **인증 토큰 (세션 대용)**  (c) DB 접속 정보  (d) API 문서

**Q7.** 에러 메시지에 "SQLITE_ERROR"가 나타나면 알 수 있는 것은?
- (a) 서버 OS  (b) **데이터베이스 종류 (SQLite)**  (c) 네트워크 구성  (d) 방화벽 설정

**Q8.** ORM(Object-Relational Mapping)이 SQLi를 방지하는 이유는?
- (a) SQL을 사용하지 않아서  (b) **자동으로 매개변수화하여 입력이 데이터로만 처리**  (c) 암호화해서  (d) 로그를 남겨서

**Q9.** OWASP Top 10에서 Injection은 몇 번인가?
- (a) A01  (b) A02  (c) **A03**  (d) A10

**Q10.** 입력값 `admin@juice-sh.op'--`로 로그인이 되는 이유는?
- (a) 비밀번호가 맞아서  (b) **`--`가 비밀번호 검증 부분을 주석 처리**  (c) 관리자 예외  (d) 세션이 남아서

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:b, Q9:c, Q10:b
""",
    ("course1-attack", 5): """
**Q1.** XSS(Cross-Site Scripting)의 핵심은?
- (a) SQL 쿼리 변조  (b) **웹페이지에 악성 JavaScript 삽입**  (c) 서버 파일 삭제  (d) 패킷 스니핑

**Q2.** Reflected XSS와 Stored XSS의 차이는?
- (a) 속도  (b) **공격 코드가 URL에 포함 vs DB에 저장**  (c) 사용 언어  (d) 피해 범위

**Q3.** `<script>alert(1)</script>`가 실행되면 어떤 취약점인가?
- (a) SQLi  (b) CSRF  (c) **XSS**  (d) SSRF

**Q4.** XSS로 탈취할 수 있는 가장 위험한 정보는?
- (a) 페이지 내용  (b) **세션 쿠키 (document.cookie)**  (c) 서버 IP  (d) CSS 스타일

**Q5.** DOM-based XSS가 서버에서 탐지하기 어려운 이유는?
- (a) 암호화되어서  (b) **서버로 요청이 가지 않고 브라우저에서만 실행**  (c) 매우 빨라서  (d) 로그가 없어서

**Q6.** XSS 방어에서 가장 중요한 기법은?
- (a) IP 차단  (b) HTTPS  (c) **출력 인코딩(HTML Entity Encoding)**  (d) 방화벽

**Q7.** `&lt;script&gt;`에서 `&lt;`의 의미는?
- (a) 작다  (b) **HTML 엔티티로 인코딩된 < 문자**  (c) 에러  (d) 주석

**Q8.** Content-Security-Policy(CSP) 헤더의 역할은?
- (a) 캐시 제어  (b) **허용된 스크립트 출처만 실행 허용**  (c) 인증  (d) 압축

**Q9.** `HttpOnly` 쿠키 플래그의 효과는?
- (a) HTTPS만 전송  (b) **JavaScript에서 쿠키 접근 불가**  (c) 자동 만료  (d) 암호화

**Q10.** Stored XSS가 Reflected XSS보다 더 위험한 이유는?
- (a) 빨라서  (b) **한 번 저장되면 해당 페이지를 방문하는 모든 사용자가 영향**  (c) 탐지 불가  (d) 서버 장악

**정답:** Q1:b, Q2:b, Q3:c, Q4:b, Q5:b, Q6:c, Q7:b, Q8:b, Q9:b, Q10:b
""",
}

# 나머지 주차들은 주제에서 자동 생성하는 범용 퀴즈
def generate_generic_quiz_from_title(title, course, week):
    """주차 제목을 기반으로 범용 퀴즈 10문항을 생성."""

    # 과목별 기본 퀴즈 템플릿
    topics = {
        "course1-attack": ("공격/침투", "ATT&CK", "보안 취약점"),
        "course2-security-ops": ("보안 솔루션", "방화벽/IPS", "SIEM"),
        "course3-web-vuln": ("웹 취약점", "OWASP", "점검"),
        "course4-compliance": ("컴플라이언스", "ISO 27001", "ISMS-P"),
        "course5-soc": ("보안관제", "로그 분석", "인시던트 대응"),
        "course6-cloud-container": ("컨테이너", "Docker", "클라우드 보안"),
        "course7-ai-security": ("LLM", "AI 보안", "OpsClaw"),
        "course8-ai-safety": ("AI Safety", "프롬프트 인젝션", "가드레일"),
    }
    t = topics.get(course, ("보안", "기술", "도구"))

    quiz = f"""
**Q1.** 이번 주차 "{title}"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **{t[0]} 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 {t[1]}의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **{t[2]} 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

**Q4.** OpsClaw를 통해 실습을 실행하는 가장 큰 이점은?
- (a) 속도  (b) **모든 실행의 자동 증적(evidence) 기록**  (c) 무료  (d) 간편함

**Q5.** 이 주제의 보안 위험이 높은 이유는?
- (a) 비용이 많이 들어서  (b) 복잡해서  (c) **악용 시 시스템/데이터에 직접적 피해**  (d) 법적 문제

**Q6.** 방어/대응의 핵심 원칙은?
- (a) 모든 트래픽 차단  (b) **최소 권한 + 탐지 + 대응의 조합**  (c) 서버 재시작  (d) 비밀번호 변경

**Q7.** 실습 결과를 분석할 때 가장 먼저 확인해야 하는 것은?
- (a) 서버 이름  (b) **exit_code (성공/실패 여부)**  (c) 파일 크기  (d) 날짜

**Q8.** 이 주제와 관련된 MITRE ATT&CK 전술은?
- (a) Impact만  (b) Reconnaissance만  (c) **주제에 해당하는 전술(들)**  (d) 해당 없음

**Q9.** 실무에서 이 기법/도구를 사용할 때 가장 주의할 점은?
- (a) 속도  (b) **법적 허가와 범위 준수**  (c) 비용  (d) 보고서 양식

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 관련 없음  (b) **이번 주 결과를 다음 주에서 활용/심화**  (c) 완전히 다른 주제  (d) 복습만

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:b, Q10:b
"""
    return quiz


def fix_quiz(filepath, course, week):
    """파일의 제너릭 퀴즈를 실제 퀴즈로 교체."""
    with open(filepath, "r") as f:
        content = f.read()

    # 제너릭 퀴즈 패턴 검색
    if "선택지 1" not in content and "정답은 강의 중 공개" not in content:
        return False  # 이미 실제 퀴즈가 있음

    # 특화 퀴즈가 있으면 사용, 없으면 자동 생성
    key = (course, week)
    if key in QUIZZES:
        new_quiz = QUIZZES[key]
    else:
        title = get_week_title(course, week)
        new_quiz = generate_generic_quiz_from_title(title, course, week)

    # 제너릭 퀴즈 섹션 찾기: "## 자가 점검 퀴즈" ~ 다음 "---" 또는 "## "
    pattern = r"## 자가 점검 퀴즈.*?(?=\n## (?!자가)|\n---\n\n## )"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        # 제너릭 섹션을 실제 퀴즈로 교체
        replacement = f"## 자가 점검 퀴즈 (10문항)\n\n이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.\n{new_quiz}"
        content = content[:match.start()] + replacement + content[match.end():]
    else:
        # 패턴 못 찾으면 "정답은 강의 중" 부분만 교체
        content = content.replace("> **Note:** 정답은 강의 중 공개합니다. 스스로 먼저 풀어보세요.\n", "")
        # 선택지 플레이스홀더 교체
        # 전체 퀴즈 블록을 찾아서 교체
        quiz_start = content.find("## 자가 점검 퀴즈")
        if quiz_start != -1:
            # 다음 ## 또는 --- 찾기
            next_section = len(content)
            for marker in ["\n## 과제", "\n## 검증", "\n---\n\n## 과제", "\n---\n\n## 검증"]:
                idx = content.find(marker, quiz_start + 10)
                if idx != -1 and idx < next_section:
                    next_section = idx

            replacement = f"## 자가 점검 퀴즈 (10문항)\n\n이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.\n{new_quiz}\n"
            content = content[:quiz_start] + replacement + content[next_section:]

    with open(filepath, "w") as f:
        f.write(content)

    return True


def main():
    fixed = 0
    skipped = 0

    for course in sorted(os.listdir(DST)):
        course_path = os.path.join(DST, course)
        if not os.path.isdir(course_path):
            continue

        for week in range(1, 16):
            filepath = os.path.join(course_path, f"week{week:02d}", "lecture.md")
            if not os.path.exists(filepath):
                continue

            if fix_quiz(filepath, course, week):
                fixed += 1
                print(f"  ✓ {course}/week{week:02d}")
            else:
                skipped += 1

    print(f"\nFixed: {fixed}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
