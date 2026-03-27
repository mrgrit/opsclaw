# Week 15: 기말 — 종합 웹취약점 점검 프로젝트

## 학습 목표
- 14주간 배운 모든 점검 기법을 종합하여 실제 웹 애플리케이션을 점검한다
- 전문 수준의 취약점 점검 보고서를 작성한다
- OWASP Testing Guide 기반 체계적 점검 절차를 수행한다

## 기말 시험 구성

### 대상: JuiceShop (http://10.20.30.80:3000)

### 점검 범위
1. 정보수집 (Week 03)
2. 인증/세션 관리 (Week 04)
3. SQL Injection (Week 05)
4. XSS/CSRF (Week 06)
5. 파일/명령어 주입 (Week 07)
6. 접근제어 (Week 09)
7. 암호화/통신 보안 (Week 10)
8. 에러 처리/정보 노출 (Week 11)
9. API 보안 (Week 12)

### 채점 기준 (100점)

| 항목 | 배점 | 기준 |
|------|------|------|
| 취약점 발견 수 | 30점 | 10개 이상 만점 |
| CVSS 점수 정확성 | 15점 | 각 취약점 CVSS 산정 |
| 재현 절차 | 20점 | 명령어 단위 재현 가능 |
| 권고사항 | 15점 | 실현 가능한 보완 방안 |
| 보고서 품질 | 20점 | 체계적 구성, 명확한 서술 |

### 보고서 형식

```markdown
# 웹 취약점 점검 보고서

## 1. 개요
- 점검 대상, 범위, 기간, 점검자

## 2. 총평
- 전체 취약점 현황 요약, 위험도 분포

## 3. 취약점 상세
### 3.1 [취약점명]
- 위험도: Critical/High/Medium/Low
- CVSS: X.X
- 위치: URL/파라미터
- 재현 절차: (명령어 단위)
- 영향: 
- 권고사항:

## 4. 결론 및 권고
```

### 실습 절차

```bash
# 1. OpsClaw 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"final-vuln-assessment","request_text":"기말 종합 점검","master_mode":"external"}'

# 2. Stage 전환
curl -s -X POST http://localhost:8000/projects/{id}/plan -H "X-API-Key: opsclaw-api-key-2026"
curl -s -X POST http://localhost:8000/projects/{id}/execute -H "X-API-Key: opsclaw-api-key-2026"

# 3. 점검 실행 (dispatch 또는 execute-plan 활용)
# 모든 점검 활동을 OpsClaw를 통해 실행하여 evidence 자동 기록

# 4. 결과 확인
curl -s http://localhost:8000/projects/{id}/evidence/summary \
  -H "X-API-Key: opsclaw-api-key-2026"

# 5. 완료보고
curl -s -X POST http://localhost:8000/projects/{id}/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"summary":"기말 점검 완료","outcome":"success","work_details":["..."]}'
```

## 제출물
1. 취약점 점검 보고서 (PDF 또는 Markdown)
2. OpsClaw 프로젝트 ID (evidence 자동 확인용)
3. 재현 스크립트 (모든 취약점 재현 가능)

## 다음 학기 예고
보안시스템 운영 (Course 2) 또는 보안관제 (Course 5) 수강 권장
