# 네트워크 잠금 — 보안 실험 인프라 준비

**실행일:** 2026-03-25
**목적:** wifi 우회 경로 차단, 모든 외부 통신을 방화벽(secu) 게이트웨이 경유로 강제

## 최종 네트워크 토폴로지

```
인터넷 ←→ [secu enp1s0/192.168.0.113] ←FW+IPS→ [enp4s0/10.20.30.1]
                                                       |
                                              L2 Switch (스위칭허브)
                                                       |
                                    ┌──────────┬───────┴────────┐
                                    |          |                |
                              [web]        [siem]          [opsclaw]
                           10.20.30.80   10.20.30.100    10.20.30.201
                           wifi OFF      wifi OFF        wifi ON (예외)
```

## 서버별 상태

| 서버 | wifi | 내부 IP | 외부 경로 | 비고 |
|------|------|---------|---------|------|
| secu | **DOWN** | 10.20.30.1 (enp4s0) | enp1s0 → 192.168.0.1 직접 | 게이트웨이/FW/IPS |
| web | **DOWN** | 10.20.30.80 (enp1s0) | → 10.20.30.1 (secu IPS 경유) | netplan 영구 설정 |
| siem | **DOWN** | 10.20.30.100 (enp1s0) | → 10.20.30.1 (secu IPS 경유) | netplan 영구 설정 |
| opsclaw | **UP** | 10.20.30.201 (enp1s0) | wlp3s0 + enp1s0 이중 | 비상/외부공격 실험용 |

## 수행 작업

1. secu: nftables 최종 설정 (input enp4s0 허용, forward NFQUEUE, NAT masquerade)
2. secu: wifi(wlp3s0) 비활성화
3. web/siem: enp4s0 중복 IP 제거 (DOWN 인터페이스)
4. web/siem: wifi 비활성화 (rfkill block + nmcli radio off + ip link down)
5. web/siem: netplan 영구 설정 (default via 10.20.30.1, DNS 8.8.8.8)
6. Suricata NFQ mode: accept 활성화 (패킷 통과 허용)
7. 인터넷 연결 검증 (web/siem → 8.8.8.8 ping 성공)

## 발견 및 수정 이슈

| 이슈 | 원인 | 해결 |
|------|------|------|
| 내부망 ping 실패 | enp4s0에 중복 IP (DOWN 상태) | ip addr del로 제거 |
| Suricata NFQUEUE 패킷 드롭 | nfq.mode: accept 주석처리 | sed로 활성화 후 재시작 |
| netplan이 wifi 재활성화 | 기존 NetworkManager 설정 잔존 | 01-network-manager-all.yaml 삭제 |

## OpsClaw 위임 준수

secu nftables 적용, web/siem wifi 비활성화 — 모두 OpsClaw execute-plan(parallel) 경유 ✅
