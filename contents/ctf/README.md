# OpsClaw CTF — 보안 교육 실습 플랫폼

## 개요
OpsClaw 보안 교육과정(8과목 120강)과 소설(10권 120장)을 기반으로 한 실습형 CTF 플랫폼.
학생이 실제 서버(v-secu/v-web/v-siem)에서 OpsClaw를 이용하여 작업하고,
그 증적(evidence)이 자동으로 기록되어 실습 검증의 근거가 된다.

## 아키텍처

```
학생 → CTFd (문제 확인) → OpsClaw (실습 수행) → SubAgent (서버 실행)
                                    ↓
                              Evidence (증적 기록)
                                    ↓
                              FLAG 생성/검증
```

## 시작하기

```bash
# CTFd 실행
cd contents/ctf
docker compose up -d

# 접속: http://localhost:8080
# 초기 설정에서 관리자 계정 생성
```

## 서버 구성

| 서버 | IP | 역할 | SubAgent |
|------|----|------|----------|
| opsclaw | 192.168.0.107 | Control Plane + CTFd | localhost:8000 |
| v-secu | 192.168.0.108 | 방화벽/IPS (nftables, Suricata) | :8002 |
| v-web | 192.168.0.110 | 웹서버 (Apache, JuiceShop) | :8002 |
| v-siem | 192.168.0.109 | SIEM (Wazuh) | :8002 |

## 문제 유형

1. **실습형**: OpsClaw dispatch로 실제 서버에서 작업 수행
2. **분석형**: 로그/경보 분석 후 답 제출
3. **코드형**: 보안 룰/스크립트 작성 후 검증

## 문제 추가

```bash
# challenges/ 디렉토리에 YAML 파일 추가 후:
python3 scripts/register_challenges.py --ctfd-url http://localhost:8080 --token <admin-token>
```

## 과목별 문제 분류

| 디렉토리 | 과목 | 주제 |
|---------|------|------|
| course1/ | 해킹/공격 | SQLi, XSS, 권한상승, 침투테스트 |
| course2/ | 보안 솔루션 | nftables, Suricata, Wazuh, WAF |
| course3/ | 웹취약점 점검 | OWASP, 자동화 도구, 보고서 |
| course4/ | 컴플라이언스 | ISO 27001, ISMS-P, SOC 2 |
| course5/ | SOC 관제 | 로그 분석, IR, SIGMA, CTI |
| course6/ | 클라우드/컨테이너 | Docker, K8s, 클라우드 보안 |
| course7/ | AI 보안 | OpsClaw, Ollama, 에이전트 보안 |
| course8/ | AI Safety | 탈옥, 가드레일, Red Teaming |
