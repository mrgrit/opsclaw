"""중앙서버 ↔ 엣지 시스템 통신 프로토콜"""
from __future__ import annotations
import os
import time
from dataclasses import dataclass, field
from typing import Any
import httpx

@dataclass
class InstanceInfo:
    """인스턴스 등록 정보"""
    instance_id: str
    instance_type: str  # "opsclaw" | "bastion" | "ccc"
    name: str
    api_url: str
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class HeartbeatPayload:
    """하트비트 페이로드"""
    instance_id: str
    timestamp: float = field(default_factory=time.time)
    status: str = "healthy"  # healthy | degraded | maintenance
    metrics: dict[str, Any] = field(default_factory=dict)  # cpu, mem, disk, agents

@dataclass
class BlockSyncPayload:
    """블록체인 블록 동기화 페이로드"""
    instance_id: str
    agent_id: str
    block_index: int
    block_hash: str
    prev_hash: str
    task_id: str | None = None
    project_id: str | None = None
    nonce: int = 0
    difficulty: int = 4
    timestamp: str = ""
    reward_amount: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CTFSubmission:
    """CTF 플래그 제출"""
    instance_id: str
    student_id: str
    challenge_id: str
    flag: str
    timestamp: float = field(default_factory=time.time)

class CentralProtocol:
    """중앙서버 통신 클라이언트"""

    def __init__(self, central_url: str | None = None, api_key: str | None = None, instance_id: str | None = None):
        self.central_url = (central_url or os.getenv("CENTRAL_SERVER_URL", "http://localhost:7000")).rstrip("/")
        self.api_key = api_key or os.getenv("CENTRAL_API_KEY", "")
        self.instance_id = instance_id or os.getenv("INSTANCE_ID", "")
        self._client = httpx.Client(timeout=30.0)

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        if self.instance_id:
            h["X-Instance-ID"] = self.instance_id
        return h

    # -- 인스턴스 관리 --
    def register(self, info: InstanceInfo) -> dict:
        """인스턴스 등록"""
        from dataclasses import asdict
        r = self._client.post(f"{self.central_url}/instances/register", json=asdict(info), headers=self._headers())
        r.raise_for_status()
        return r.json()

    def heartbeat(self, payload: HeartbeatPayload) -> dict:
        """하트비트 전송"""
        from dataclasses import asdict
        r = self._client.post(f"{self.central_url}/instances/heartbeat", json=asdict(payload), headers=self._headers())
        r.raise_for_status()
        return r.json()

    # -- 블록체인 동기화 --
    def sync_block(self, payload: BlockSyncPayload) -> dict:
        """블록 동기화 (엣지→중앙)"""
        from dataclasses import asdict
        r = self._client.post(f"{self.central_url}/blockchain/sync", json=asdict(payload), headers=self._headers())
        r.raise_for_status()
        return r.json()

    def get_unified_leaderboard(self) -> dict:
        """통합 리더보드 조회"""
        r = self._client.get(f"{self.central_url}/blockchain/leaderboard", headers=self._headers())
        r.raise_for_status()
        return r.json()

    # -- CTF --
    def list_challenges(self) -> list[dict]:
        """CTF 문제 목록"""
        r = self._client.get(f"{self.central_url}/ctf/challenges", headers=self._headers())
        r.raise_for_status()
        return r.json()

    def submit_flag(self, submission: CTFSubmission) -> dict:
        """플래그 제출"""
        from dataclasses import asdict
        r = self._client.post(f"{self.central_url}/ctf/submit", json=asdict(submission), headers=self._headers())
        r.raise_for_status()
        return r.json()

    def get_scoreboard(self) -> dict:
        """CTF 스코어보드"""
        r = self._client.get(f"{self.central_url}/ctf/scoreboard", headers=self._headers())
        r.raise_for_status()
        return r.json()

    # -- 배포 패키지 --
    def list_packages(self, pkg_type: str | None = None) -> list[dict]:
        """배포 패키지 목록"""
        params = {"type": pkg_type} if pkg_type else {}
        r = self._client.get(f"{self.central_url}/packages/", params=params, headers=self._headers())
        r.raise_for_status()
        return r.json()

    def download_package(self, name: str, version: str = "latest") -> bytes:
        """패키지 다운로드"""
        r = self._client.get(f"{self.central_url}/packages/{name}/{version}", headers=self._headers())
        r.raise_for_status()
        return r.content
