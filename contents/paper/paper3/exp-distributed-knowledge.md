# 분산 지식 아키텍처 실험 결과

**실행일:** 2026-03-25
**프로젝트:** purple-auto-knowledge
**Red:** gemma3:12b + opsclaw.json 로컬 지식
**Blue:** llama3.1:8b + siem.json 로컬 지식

---

## 이전 실험 (지식 없음) vs 현재 실험 (로컬 지식 주입)

### Blue Team 비교

| 항목 | v1 (지식 없음) | v2 (로컬 지식) | 개선 |
|------|--------------|--------------|------|
| SSH 사용 | ❌ `ssh siem@...` (비밀번호 실패) | ✅ `sshpass -p1 ssh ...` | **SSH 접속 성공** |
| Wazuh 상태 확인 | ❌ 실패 | ✅ `systemctl status wazuh-manager` 성공 | **SIEM 모니터링 시작** |
| alerts 경로 | ❌ 모름 | ✅ `/var/ossec/logs/alerts/alerts.json` 인식 | **로컬 지식 참조** |
| 룰 생성 | ❌ `wazuh-api create-rule` (환각) | △ `grep_sqli_alerts` (tools 키 혼동) | **부분 개선** |
| 총 점수 | 0/16 | ~3/16 (상태확인+경로인식) | **+3점** |

### Red Team 비교

| 항목 | v1 (지식 없음) | v2 (로컬 지식) | 개선 |
|------|--------------|--------------|------|
| Steps | 4 | **8** | 더 끈질긴 공격 시도 |
| 정찰 | ✅ | ✅ | 동일 |
| SQLi | ❌ (이스케이핑) | ❌ (이스케이핑, 하지만 4회 시도) | 12B 한계 유지 |
| FTP 확인 | ❌ (미도달) | ❌ (SQLi에서 막힘) | — |
| API 접근 | ❌ (미도달) | △ `/api/Users` 시도 (JWT 없어 실패) | **새 공격 경로 시도** |

### 로컬 지식 자동 저장 확인

미션 완료 후 siem.json에 자동으로 경험이 추가됨:
```
"updated_at": "2026-03-25T14:51:40Z"  (이전: T22:00:00Z)
```
→ 성공한 명령이 experiences 배열에 자동 추가되어 다음 미션에서 참조 가능

---

## 핵심 발견

1. **SSH 패턴 학습 성공:** 로컬 지식의 tools 섹션에서 sshpass 패턴을 학습하여 Blue가 원격 서버에 올바르게 접속
2. **경로 인식 성공:** `/var/ossec/logs/alerts/alerts.json` 등 Wazuh 경로를 로컬 지식에서 참조
3. **tools 키 혼동:** `grep_sqli_alerts`를 실제 명령어가 아닌 도구 이름(키)으로 인식 → tools 포맷 개선 필요
4. **자동 저장 동작:** 미션 성공 결과가 local_knowledge.json에 자동 추가 → 누적 학습
5. **Red 지속성 향상:** 로컬 지식의 경험(이전 SQLi 성공 사례)을 참조하여 더 많은 변형 시도

## 미해결

- Blue의 `grep_sqli_alerts` 혼동 → tools에 설명 추가 또는 포맷 변경 필요
- Red SQLi 이스케이핑 → 12B 모델 한계, Playbook 직접 실행이 근본 해결
