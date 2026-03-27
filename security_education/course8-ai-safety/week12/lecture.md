# Week 12: AI 윤리와 규제

## 학습 목표
- EU AI Act의 주요 내용과 위험 분류 체계를 이해한다
- NIST AI Risk Management Framework를 분석한다
- 한국의 AI 관련 법안과 규제 동향을 파악한다
- AI 윤리 원칙을 실무에 적용하는 방법을 이해한다

---

## 1. AI 위험과 윤리적 문제

### 1.1 AI 사고 사례

| 사례 | 년도 | 문제 | 교훈 |
|------|------|------|------|
| Tay 챗봇 | 2016 | 혐오 발언 학습 | 데이터 오염 방어 필요 |
| Uber 자율주행 사고 | 2018 | 보행자 사망 | 안전 임계값 설계 |
| GPT 할루시네이션 | 2023 | 허위 법률 판례 인용 | 사실 검증 필수 |
| Deepfake 선거 개입 | 2024 | 허위 음성 생성 | 콘텐츠 인증 필요 |
| AI 채용 편향 | 2018 | 성별 차별 | 공정성 감사 필수 |

### 1.2 AI 윤리 5대 원칙

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
principles = [
    ("공정성 (Fairness)", "AI가 특정 집단을 차별하지 않아야 한다", "편향 감사, 공정성 메트릭"),
    ("투명성 (Transparency)", "AI의 결정 과정을 설명할 수 있어야 한다", "XAI, 모델 카드"),
    ("프라이버시 (Privacy)", "개인정보를 보호해야 한다", "차분 프라이버시, PII 마스킹"),
    ("안전성 (Safety)", "AI가 해를 끼치지 않아야 한다", "가드레일, 안전 테스트"),
    ("책임성 (Accountability)", "AI 결정에 대한 책임 소재가 명확해야 한다", "감사 로그, 거버넌스"),
]

print("=== AI 윤리 5대 원칙 ===\n")
for name, desc, impl in principles:
    print(f"  {name}")
    print(f"    정의: {desc}")
    print(f"    구현: {impl}\n")

PYEOF
ENDSSH
```

---

## 2. EU AI Act

### 2.1 위험 기반 분류 체계

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
risk_levels = [
    {
        "level": "허용 불가 위험 (Unacceptable)",
        "examples": ["사회적 점수 시스템", "실시간 원격 생체 인식 (일부)", "조작적 AI"],
        "action": "전면 금지",
    },
    {
        "level": "고위험 (High-risk)",
        "examples": ["의료 진단 AI", "채용/교육 AI", "법 집행 AI", "신용 평가"],
        "action": "적합성 평가, 등록, 모니터링 의무",
    },
    {
        "level": "제한적 위험 (Limited)",
        "examples": ["챗봇", "Deepfake 생성", "감정 인식"],
        "action": "투명성 의무 (AI임을 고지)",
    },
    {
        "level": "최소 위험 (Minimal)",
        "examples": ["스팸 필터", "게임 AI", "검색 추천"],
        "action": "특별 규제 없음",
    },
]

print("=== EU AI Act 위험 분류 체계 ===\n")
for r in risk_levels:
    print(f"{r['level']}")
    print(f"  예시: {', '.join(r['examples'])}")
    print(f"  규제: {r['action']}\n")

PYEOF
ENDSSH
```

### 2.2 고위험 AI 의무사항

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
obligations = [
    ("리스크 관리 시스템", "AI 시스템 생애주기 전반의 리스크 관리"),
    ("데이터 거버넌스", "학습 데이터 품질, 편향 검증, 문서화"),
    ("기술 문서화", "설계, 개발, 테스트 과정 문서화"),
    ("기록 보관", "자동 로깅, 감사 추적"),
    ("투명성", "사용자에게 AI 사용 고지, 설명 가능성"),
    ("인간 감독", "인간이 AI를 감독하고 개입할 수 있는 수단"),
    ("정확성/강건성/보안", "적절한 성능, 적대적 공격 방어, 사이버보안"),
    ("적합성 평가", "시장 출시 전 적합성 평가 수행"),
]

print("=== 고위험 AI 시스템 의무사항 ===\n")
for i, (name, desc) in enumerate(obligations, 1):
    print(f"  {i}. {name}")
    print(f"     {desc}\n")

print("위반 시 과징금: 최대 3,500만 유로 또는 전 세계 매출의 7%")

PYEOF
ENDSSH
```

---

## 3. NIST AI Risk Management Framework

### 3.1 AI RMF 구조

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
nist_ai_rmf = {
    "GOVERN (관리)": [
        "AI 리스크 관리 정책 수립",
        "역할과 책임 정의",
        "조직 문화에 AI 윤리 통합",
    ],
    "MAP (매핑)": [
        "AI 시스템의 맥락과 용도 파악",
        "이해관계자 식별",
        "위험과 영향 범위 매핑",
    ],
    "MEASURE (측정)": [
        "AI 시스템 성능/편향/안전성 측정",
        "정량적 메트릭 수집",
        "지속적 모니터링",
    ],
    "MANAGE (관리)": [
        "식별된 리스크에 대한 대응 계획",
        "리스크 완화 조치 실행",
        "잔여 리스크 수용 여부 결정",
    ],
}

print("=== NIST AI RMF 핵심 기능 ===\n")
for function, activities in nist_ai_rmf.items():
    print(f"{function}")
    for a in activities:
        print(f"  - {a}")
    print()

PYEOF
ENDSSH
```

---

## 4. 한국 AI 규제 동향

### 4.1 주요 법안/정책

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
korea_ai_policy = [
    {
        "name": "인공지능 기본법 (2024 제정)",
        "key_points": [
            "AI 윤리 원칙 법제화",
            "고위험 AI 영향평가 의무",
            "AI 안전성 확보 조치",
            "국가인공지능위원회 설치",
        ],
    },
    {
        "name": "개인정보보호법 (AI 관련)",
        "key_points": [
            "자동화된 의사결정에 대한 설명 요구권",
            "프로파일링 거부권",
            "AI 학습 데이터 내 개인정보 보호",
        ],
    },
    {
        "name": "정보통신망법",
        "key_points": [
            "AI 생성 콘텐츠 표시 의무",
            "딥페이크 규제",
        ],
    },
    {
        "name": "ISMS-P 인증 (AI 확장)",
        "key_points": [
            "AI 시스템 보안 관리 체계",
            "AI 모델 라이프사이클 보안",
        ],
    },
]

print("=== 한국 AI 규제 동향 ===\n")
for policy in korea_ai_policy:
    print(f"{policy['name']}")
    for kp in policy['key_points']:
        print(f"  - {kp}")
    print()

PYEOF
ENDSSH
```

---

## 5. AI 윤리 실무 적용

### 5.1 AI 시스템 윤리 체크리스트

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
checklist = {
    "개발 단계": [
        "학습 데이터에 편향이 없는지 검증했는가?",
        "프라이버시 영향평가를 수행했는가?",
        "안전성 테스트(Red Teaming)를 수행했는가?",
        "모델 카드(Model Card)를 작성했는가?",
    ],
    "배포 단계": [
        "사용자에게 AI 사용을 고지하는가?",
        "인간 감독 메커니즘이 있는가?",
        "출력에 유해 콘텐츠 필터가 적용되는가?",
        "감사 로그가 기록되는가?",
    ],
    "운영 단계": [
        "모델 성능/편향을 지속 모니터링하는가?",
        "사용자 피드백을 수집하고 반영하는가?",
        "인시던트 대응 계획이 있는가?",
        "정기적으로 윤리 감사를 수행하는가?",
    ],
}

print("=== AI 시스템 윤리 체크리스트 ===\n")
total = 0
for stage, items in checklist.items():
    print(f"{stage}")
    for item in items:
        print(f"  [ ] {item}")
        total += 1
    print()
print(f"총 {total}개 항목")

PYEOF
ENDSSH
```

### 5.2 LLM으로 윤리적 판단 시뮬레이션

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "AI 윤리 전문가입니다. EU AI Act와 한국 AI 기본법 기준으로 판단합니다."},
      {"role": "user", "content": "다음 AI 시스템의 위험 등급을 EU AI Act 기준으로 분류하고, 필요한 규제 조치를 제시하세요:\n\n1. 직원 채용 이력서 자동 필터링 AI\n2. 고객 서비스 챗봇\n3. 의료 영상 진단 보조 AI\n4. 이메일 스팸 필터\n5. 보안 관제 자동 대응 AI (OpsClaw)"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 핵심 정리

1. EU AI Act는 허용불가/고위험/제한적/최소 4단계 위험 분류를 적용한다
2. 고위험 AI는 리스크 관리, 데이터 거버넌스, 인간 감독 등 8가지 의무가 있다
3. NIST AI RMF는 Govern-Map-Measure-Manage 4단계 프레임워크다
4. 한국은 AI 기본법으로 고위험 AI 영향평가와 윤리 원칙을 법제화했다
5. AI 윤리는 공정성, 투명성, 프라이버시, 안전성, 책임성 5대 원칙이다
6. 개발-배포-운영 전 단계에서 윤리 체크리스트를 적용해야 한다

---

## 다음 주 예고
- Week 13: Red Teaming for AI - 체계적 AI 취약점 평가, 자동화 레드팀
