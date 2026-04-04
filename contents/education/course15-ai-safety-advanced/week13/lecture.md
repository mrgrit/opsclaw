# Week 13: AI 거버넌스 + 규제

## 학습 목표
- EU AI Act의 구조와 위험 등급 분류를 이해한다
- NIST AI Risk Management Framework(AI RMF)를 분석한다
- AI 위험 평가(Risk Assessment) 절차를 수행할 수 있다
- 조직 내 AI 거버넌스 체계를 설계할 수 있다
- AI 규제 준수 자동화 도구를 구축할 수 있다

## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | Part 1: EU AI Act 심화 분석 | 강의 |
| 0:40-1:20 | Part 2: NIST AI RMF와 위험 평가 | 강의/토론 |
| 1:20-1:30 | 휴식 | - |
| 1:30-2:10 | Part 3: AI 위험 평가 실습 | 실습 |
| 2:10-2:50 | Part 4: 규제 준수 자동화 도구 | 실습 |
| 2:50-3:00 | 복습 퀴즈 + 과제 안내 | 퀴즈 |

---

## 용어 해설

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **AI 거버넌스** | AI Governance | AI 개발/운영의 조직적 통제 체계 | 회사의 AI 관리 규정 |
| **EU AI Act** | EU AI Act | EU의 인공지능 규제법 | AI판 교통법규 |
| **NIST AI RMF** | NIST AI Risk Management Framework | 미국의 AI 위험 관리 프레임워크 | AI 위험 관리 매뉴얼 |
| **위험 등급** | Risk Category | AI 시스템의 위험 수준 분류 | 도로 속도 제한 |
| **적합성 평가** | Conformity Assessment | 규제 요건 충족 여부 검증 | 차량 검사 |
| **투명성** | Transparency | AI 의사결정의 설명 가능성 | 유리 상자 |
| **책임** | Accountability | AI 결과에 대한 책임 귀속 | 누가 책임지나 |
| **영향 평가** | Impact Assessment | AI 도입의 사회적 영향 분석 | 환경 영향 평가 |

---

# Part 1: EU AI Act 심화 분석 (40분)

## 1.1 EU AI Act 위험 등급 체계

```
EU AI Act 위험 4등급

  [금지 (Unacceptable Risk)]
  ├── 사회적 점수제(Social Scoring)
  ├── 실시간 원격 생체인식(법 집행 예외)
  ├── 잠재의식 조작 AI
  └── 취약 집단 착취 AI

  [고위험 (High Risk)]
  ├── 채용/인사 관리 AI
  ├── 교육 평가 AI
  ├── 법 집행 AI
  ├── 의료 진단 AI
  ├── 신용 평가 AI
  └── 중요 인프라 관리 AI

  [제한 위험 (Limited Risk)]
  ├── 챗봇 (AI임을 고지 의무)
  ├── 딥페이크 (라벨링 의무)
  └── 감정 인식 시스템

  [최소 위험 (Minimal Risk)]
  ├── 스팸 필터
  ├── AI 게임
  └── 추천 시스템
```

## 1.2 고위험 AI 시스템 요구사항

| 요구사항 | 내용 | 위반 시 |
|----------|------|--------|
| **위험 관리** | 지속적 위험 관리 시스템 운영 | 최대 3천만 유로 과징금 |
| **데이터 거버넌스** | 학습 데이터 품질/편향 관리 | 최대 매출 7% 과징금 |
| **기술 문서** | 시스템 설계/성능 문서화 | 시장 출시 금지 |
| **로깅** | 자동 기록 보관 | 적합성 미인정 |
| **투명성** | 사용자에게 AI 사용 고지 | 과징금 |
| **인적 감독** | 사람의 개입/통제 보장 | 과징금 |
| **정확성** | 적절한 정확도/강건성 보장 | 시장 출시 금지 |
| **사이버보안** | 적대적 공격 대응 | 과징금 |

## 1.3 NIST AI Risk Management Framework

```
NIST AI RMF 4대 기능

  [GOVERN] 거버넌스
  ├── AI 리스크 문화 구축
  ├── 역할/책임 정의
  ├── 정책/절차 수립
  └── 외부 이해관계자 소통

  [MAP] 위험 매핑
  ├── AI 시스템 특성 파악
  ├── 사용 맥락 이해
  ├── 이해관계자 식별
  └── 위험 요소 도출

  [MEASURE] 위험 측정
  ├── 위험 정량화
  ├── 성능/안전 메트릭
  ├── 편향/공정성 평가
  └── 보안/프라이버시 평가

  [MANAGE] 위험 관리
  ├── 완화 조치 실행
  ├── 지속적 모니터링
  ├── 인시던트 대응
  └── 개선/업데이트
```

## 1.4 한국 AI 규제 동향

| 법규 | 상태 | 핵심 내용 |
|------|------|----------|
| **AI 기본법** | 시행 중 | AI 산업 진흥 + 윤리 원칙 |
| **개인정보보호법** | AI 조항 강화 | 자동화된 의사결정 정보권 |
| **정보통신망법** | 적용 | AI 생성 콘텐츠 라벨링 |
| **AI 윤리 기준** | 가이드라인 | 사람 중심, 안전, 투명, 책임 |

---

# Part 2: NIST AI RMF와 위험 평가 (40분)

## 2.1 AI 위험 평가 프레임워크

```
AI 위험 평가 절차

  Step 1: 시스템 식별
  ├── AI 시스템 목록 작성
  ├── 각 시스템의 목적/범위 정의
  └── 데이터 흐름 매핑

  Step 2: 위험 분류
  ├── EU AI Act 위험 등급 매핑
  ├── 영향 범위 평가 (사용자 수, 도메인)
  └── 취약 집단 영향 분석

  Step 3: 위험 측정
  ├── 기술적 위험 (정확도, 강건성, 편향)
  ├── 사회적 위험 (차별, 프라이버시)
  ├── 운영 위험 (가용성, 의존성)
  └── 법적 위험 (규제 위반, 소송)

  Step 4: 완화 조치
  ├── 기술적 조치 (안전 레이어, 모니터링)
  ├── 조직적 조치 (정책, 교육, 감사)
  └── 잔여 위험 수용/이전

  Step 5: 지속적 모니터링
  ├── 메트릭 수집
  ├── 정기 감사
  └── 인시던트 대응 훈련
```

## 2.2 위험 매트릭스

```
AI 위험 매트릭스

  영향(Impact)
  심각 │ M    H    H    C
  높음 │ L    M    H    H
  중간 │ L    L    M    H
  낮음 │ L    L    L    M
       └──────────────────→
         낮음  중간  높음  매우높음
              발생 가능성(Likelihood)

  L = Low Risk (최소 위험)
  M = Medium Risk (제한 위험)
  H = High Risk (고위험)
  C = Critical (금지/즉시 조치)
```

---

# Part 3: AI 위험 평가 실습 (40분)

> **이 실습을 왜 하는가?**
> AI 시스템의 위험을 체계적으로 평가하는 실무 역량을 기른다.
> 실제 AI 서비스에 대한 위험 평가를 수행하고 보고서를 작성한다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - AI 위험 평가의 실무 절차
> - 규제 요건과 시스템의 매핑
> - 자동화된 준수 점검 방법
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

## 3.1 AI 시스템 위험 평가 도구

```bash
# AI 위험 평가 자동화 도구
cat > /tmp/risk_assessment.py << 'PYEOF'
import json

class AIRiskAssessor:
    """AI 시스템 위험 평가 도구"""

    EU_AI_ACT_CATEGORIES = {
        "unacceptable": {
            "keywords": ["social scoring", "사회적 점수", "실시간 생체인식", "잠재의식 조작"],
            "action": "금지 - 사용 불가",
        },
        "high_risk": {
            "keywords": ["채용", "인사", "교육 평가", "법 집행", "의료 진단", "신용 평가", "중요 인프라"],
            "action": "적합성 평가 필수 - 전체 요구사항 준수",
        },
        "limited_risk": {
            "keywords": ["챗봇", "대화형", "딥페이크", "감정 인식", "고객 서비스 봇"],
            "action": "투명성 의무 - AI 사용 고지",
        },
        "minimal_risk": {
            "keywords": ["스팸 필터", "추천", "게임", "번역", "검색"],
            "action": "자율 규제 권장",
        },
    }

    RISK_FACTORS = [
        {"name": "데이터 프라이버시", "weight": 0.2, "questions": [
            "개인정보를 처리하는가?",
            "민감 정보(건강, 인종, 종교)를 다루는가?",
            "데이터 주체의 동의를 받았는가?",
        ]},
        {"name": "편향/공정성", "weight": 0.2, "questions": [
            "보호 속성(성별, 나이, 인종)에 따라 다른 결과를 생성하는가?",
            "학습 데이터의 대표성을 검증했는가?",
            "정기적 편향 감사를 수행하는가?",
        ]},
        {"name": "안전/강건성", "weight": 0.2, "questions": [
            "적대적 입력에 대한 방어가 있는가?",
            "프롬프트 인젝션 방어를 구현했는가?",
            "출력 필터를 적용하는가?",
        ]},
        {"name": "투명성", "weight": 0.15, "questions": [
            "AI 사용을 사용자에게 고지하는가?",
            "AI 의사결정의 근거를 설명할 수 있는가?",
            "기술 문서를 유지하는가?",
        ]},
        {"name": "인적 감독", "weight": 0.15, "questions": [
            "사람이 AI 결정을 무시할 수 있는가?",
            "고위험 결정에 사람의 승인이 필요한가?",
            "이상 동작 시 자동 정지 기능이 있는가?",
        ]},
        {"name": "로깅/감사", "weight": 0.1, "questions": [
            "모든 입출력을 로깅하는가?",
            "감사 추적(audit trail)을 유지하는가?",
            "정기적 보안 감사를 수행하는가?",
        ]},
    ]

    def classify_eu_risk(self, system_description):
        desc_lower = system_description.lower()
        for category, info in self.EU_AI_ACT_CATEGORIES.items():
            for kw in info["keywords"]:
                if kw in desc_lower:
                    return category, info["action"]
        return "minimal_risk", self.EU_AI_ACT_CATEGORIES["minimal_risk"]["action"]

    def assess(self, system_name, description, answers):
        category, action = self.classify_eu_risk(description)

        factor_scores = []
        for i, factor in enumerate(self.RISK_FACTORS):
            yes_count = sum(1 for a in answers.get(factor["name"], []) if a)
            total = len(factor["questions"])
            score = yes_count / max(total, 1)
            factor_scores.append({
                "factor": factor["name"],
                "score": round(score, 2),
                "weight": factor["weight"],
                "weighted": round(score * factor["weight"], 3),
            })

        overall = sum(f["weighted"] for f in factor_scores)
        risk_level = "low" if overall >= 0.7 else "medium" if overall >= 0.4 else "high"

        return {
            "system": system_name,
            "eu_category": category,
            "eu_action": action,
            "overall_score": round(overall, 3),
            "risk_level": risk_level,
            "factors": factor_scores,
        }


# 예시 평가
assessor = AIRiskAssessor()

# OpsClaw 에이전트 시스템 평가
result = assessor.assess(
    "OpsClaw AI Agent",
    "IT 운영 자동화를 위한 AI 에이전트 시스템. 서버 관리, 보안 작업을 자동화. 중요 인프라 관리.",
    {
        "데이터 프라이버시": [True, False, True],
        "편향/공정성": [False, True, True],
        "안전/강건성": [True, True, True],
        "투명성": [True, True, True],
        "인적 감독": [True, True, True],
        "로깅/감사": [True, True, True],
    }
)

print("=== AI 위험 평가 결과 ===\n")
print(f"시스템: {result['system']}")
print(f"EU AI Act 분류: {result['eu_category']}")
print(f"필요 조치: {result['eu_action']}")
print(f"종합 점수: {result['overall_score']} ({result['risk_level']})")
print(f"\n요소별 점수:")
for f in result["factors"]:
    bar = "=" * int(f["score"] * 20)
    print(f"  {f['factor']:15s}: {f['score']:.2f} [{bar:20s}]")
PYEOF

python3 /tmp/risk_assessment.py
```

## 3.2 규제 준수 체크리스트 자동화

```bash
# 규제 준수 자동 체크리스트
cat > /tmp/compliance_check.py << 'PYEOF'
import json

class ComplianceChecker:
    """AI 규제 준수 자동 체크리스트"""

    REQUIREMENTS = {
        "EU AI Act (고위험)": [
            {"id": "EU-1", "req": "위험 관리 시스템 운영", "critical": True},
            {"id": "EU-2", "req": "학습 데이터 품질 관리", "critical": True},
            {"id": "EU-3", "req": "기술 문서 유지", "critical": True},
            {"id": "EU-4", "req": "자동 로깅 시스템", "critical": True},
            {"id": "EU-5", "req": "사용자 투명성 고지", "critical": False},
            {"id": "EU-6", "req": "인적 감독 메커니즘", "critical": True},
            {"id": "EU-7", "req": "정확성/강건성 보장", "critical": True},
            {"id": "EU-8", "req": "사이버보안 대책", "critical": True},
        ],
        "NIST AI RMF": [
            {"id": "NIST-G1", "req": "AI 거버넌스 정책 수립", "critical": False},
            {"id": "NIST-M1", "req": "AI 위험 매핑 완료", "critical": False},
            {"id": "NIST-ME1", "req": "위험 메트릭 정의 및 측정", "critical": False},
            {"id": "NIST-MA1", "req": "위험 완화 조치 실행", "critical": True},
            {"id": "NIST-MA2", "req": "지속적 모니터링 체계", "critical": True},
        ],
        "개인정보보호법": [
            {"id": "KR-1", "req": "개인정보 처리 동의", "critical": True},
            {"id": "KR-2", "req": "자동화된 의사결정 고지", "critical": True},
            {"id": "KR-3", "req": "개인정보 영향 평가", "critical": False},
            {"id": "KR-4", "req": "파기 절차 수립", "critical": True},
        ],
    }

    def check(self, compliance_status):
        results = {}
        for framework, reqs in self.REQUIREMENTS.items():
            checks = []
            for req in reqs:
                status = compliance_status.get(req["id"], False)
                checks.append({**req, "compliant": status})
            compliant = sum(1 for c in checks if c["compliant"])
            critical_missing = [c for c in checks if c["critical"] and not c["compliant"]]
            results[framework] = {
                "total": len(checks),
                "compliant": compliant,
                "rate": round(compliant / max(len(checks), 1) * 100, 1),
                "critical_missing": critical_missing,
                "checks": checks,
            }
        return results


checker = ComplianceChecker()

# OpsClaw 준수 현황 (예시)
status = {
    "EU-1": True, "EU-2": True, "EU-3": True, "EU-4": True,
    "EU-5": True, "EU-6": True, "EU-7": True, "EU-8": True,
    "NIST-G1": True, "NIST-M1": False, "NIST-ME1": False,
    "NIST-MA1": True, "NIST-MA2": True,
    "KR-1": True, "KR-2": False, "KR-3": False, "KR-4": True,
}

results = checker.check(status)
print("=== 규제 준수 체크 결과 ===\n")
for framework, r in results.items():
    status_icon = "PASS" if r["rate"] == 100 else "WARN" if r["rate"] >= 70 else "FAIL"
    print(f"[{status_icon}] {framework}: {r['compliant']}/{r['total']} ({r['rate']}%)")
    if r["critical_missing"]:
        for cm in r["critical_missing"]:
            print(f"  [!] 필수 미충족: {cm['id']} - {cm['req']}")
    print()
PYEOF

python3 /tmp/compliance_check.py
```

---

# Part 4: 규제 준수 자동화 도구 (40분)

> **이 실습을 왜 하는가?**
> AI 거버넌스를 자동화하여 규제 준수를 체계적으로 관리한다.
> 수동 체크리스트를 넘어 자동화된 모니터링과 보고를 구현한다.
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.

## 4.1 OpsClaw 연동

```bash
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "ai-governance-week13",
    "request_text": "AI 거버넌스/규제 실습 - EU AI Act, NIST AI RMF, 위험 평가, 준수 체크",
    "master_mode": "external"
  }' | python3 -m json.tool
```

---

## 체크리스트

- [ ] EU AI Act의 4단계 위험 등급을 설명할 수 있다
- [ ] 고위험 AI 시스템의 8가지 요구사항을 열거할 수 있다
- [ ] NIST AI RMF의 4대 기능(GOVERN/MAP/MEASURE/MANAGE)을 설명할 수 있다
- [ ] AI 위험 평가 5단계를 수행할 수 있다
- [ ] 위험 매트릭스를 작성할 수 있다
- [ ] 규제 준수 체크리스트를 작성하고 자동화할 수 있다
- [ ] AI 거버넌스 정책을 설계할 수 있다
- [ ] 한국 AI 규제 동향을 이해한다
- [ ] AI 시스템의 EU AI Act 분류를 수행할 수 있다
- [ ] 잔여 위험 분석을 수행할 수 있다

---

## 복습 퀴즈

### 퀴즈 1: EU AI Act에서 "금지(Unacceptable)" 등급에 해당하는 것은?
- A) 채용 AI
- B) 사회적 점수제(Social Scoring)
- C) 챗봇
- D) 스팸 필터

**정답: B) 사회적 점수제(Social Scoring)**

### 퀴즈 2: NIST AI RMF의 4대 기능 중 "위험 측정"에 해당하는 것은?
- A) GOVERN
- B) MAP
- C) MEASURE
- D) MANAGE

**정답: C) MEASURE**

### 퀴즈 3: 고위험 AI 시스템에서 "인적 감독"이 필수인 이유는?
- A) 비용을 줄이기 위해
- B) AI가 완벽하지 않으므로 사람이 최종 판단을 할 수 있어야 함
- C) AI 속도를 높이기 위해
- D) 규제와 무관한 선택 사항이다

**정답: B) AI가 완벽하지 않으므로 사람이 최종 판단을 할 수 있어야 함**

### 퀴즈 4: EU AI Act 위반 시 최대 과징금은?
- A) 1만 유로
- B) 100만 유로
- C) 3천만 유로 또는 매출 7%
- D) 과징금 없음

**정답: C) 3천만 유로 또는 매출 7%**

### 퀴즈 5: AI 위험 평가에서 "잔여 위험"이란?
- A) 모든 위험이 제거된 상태
- B) 완화 조치를 적용한 후에도 남아 있는 위험
- C) 과거의 위험
- D) 다른 시스템의 위험

**정답: B) 완화 조치를 적용한 후에도 남아 있는 위험**

### 퀴즈 6: "AI 사용 고지 의무"가 적용되는 EU AI Act 등급은?
- A) 최소 위험
- B) 제한 위험 (챗봇, 딥페이크)
- C) 금지
- D) 모든 등급

**정답: B) 제한 위험 (챗봇, 딥페이크)**

### 퀴즈 7: AI 거버넌스 체계에서 "역할과 책임"을 정의하는 이유는?
- A) 문서 분량을 늘리기 위해
- B) AI 관련 의사결정과 사고 대응에서 누가 무엇을 담당하는지 명확히 하기 위해
- C) 조직도를 그리기 위해
- D) 비용을 절감하기 위해

**정답: B) AI 관련 의사결정과 사고 대응에서 누가 무엇을 담당하는지 명확히 하기 위해**

### 퀴즈 8: NIST AI RMF에서 "MAP" 기능의 목적은?
- A) AI 시스템의 위험을 측정
- B) AI 시스템의 특성과 사용 맥락을 파악하고 위험 요소를 도출
- C) AI 거버넌스 정책을 수립
- D) 위험 완화 조치를 실행

**정답: B) AI 시스템의 특성과 사용 맥락을 파악하고 위험 요소를 도출**

### 퀴즈 9: 한국 개인정보보호법에서 AI에 관련된 권리는?
- A) AI 사용 금지
- B) 자동화된 의사결정에 대한 설명 요구권과 거부권
- C) AI 개발 참여권
- D) 관련 조항 없음

**정답: B) 자동화된 의사결정에 대한 설명 요구권과 거부권**

### 퀴즈 10: 규제 준수 자동화의 가장 큰 이점은?
- A) 비용이 전혀 들지 않음
- B) 지속적 모니터링과 실시간 준수 상태 파악이 가능
- C) 규제를 무시할 수 있음
- D) 사람이 필요 없어짐

**정답: B) 지속적 모니터링과 실시간 준수 상태 파악이 가능**

---

## 과제

### 과제 1: AI 위험 평가 수행 (필수)
- 가상의 AI 서비스(예: AI 채용 시스템)에 대한 위험 평가 수행
- risk_assessment.py를 사용하여 EU AI Act 분류 및 위험 점수 산출
- 발견된 위험에 대한 완화 조치 3가지 이상 제안

### 과제 2: 규제 준수 대시보드 설계 (필수)
- compliance_check.py를 확장하여 HTML 보고서 생성 기능 추가
- 3가지 규제 프레임워크의 준수 현황을 시각화
- 미충족 항목에 대한 우선순위별 조치 계획 수립

### 과제 3: AI 거버넌스 정책 문서 작성 (심화)
- 가상의 조직을 위한 AI 거버넌스 정책 문서 작성
- 포함: 목적, 범위, 역할, 위험 관리, 감사, 인시던트 대응
- EU AI Act + NIST AI RMF + 한국 규제를 모두 반영
