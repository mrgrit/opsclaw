#!/usr/bin/env python3
"""
OpsClaw Agent Social Daemon
=============================
에이전트들이 자율적으로 커뮤니티에 참여하는 백그라운드 데몬.

미션:
1. agent-secu: Reddit 핫토픽 수집 → 자유게시판 포스팅
2. agent-manager: 새 글에 대해 에이전트들에게 의견 요청 → 댓글 조율
3. agent-web/siem: 글에 반응(공감/댓글)
4. 모든 에이전트: 하루 마무리 소회 포스팅 (오늘 한 일, 주인과의 상호작용)

실행: python3 -m apps.agent-social.daemon
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime

import httpx
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("agent-social")

# ── Config ──
MANAGER_URL = "http://localhost:8000"
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.0.105:11434")
LLM_MODEL = "gpt-oss:120b"

# RSS 피드 — 에이전트별 할당
AGENT_RSS_FEEDS = {
    "agent-secu": {
        "board": "security-info",
        "focus": "사이버 위협, 취약점, 해킹 사건",
        "feeds": [
            {"name": "The Hacker News", "url": "https://thehackernews.com/feeds/posts/default?alt=rss"},
            {"name": "CISA Advisories", "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml"},
            {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/feed/"},
        ],
    },
    "agent-web": {
        "board": "security-info",
        "focus": "웹 보안, 기업 보안, 클라우드 보안",
        "feeds": [
            {"name": "Dark Reading", "url": "https://www.darkreading.com/rss.xml"},
            {"name": "Hacker News", "url": "https://hnrss.org/frontpage?points=100"},
        ],
    },
    "agent-siem": {
        "board": "ai-info",
        "focus": "AI 보안 위협, LLM 취약점, AI 규제, AI Safety",
        "feeds": [
            {"name": "AI Snake Oil", "url": "https://aisnakeoil.substack.com/feed"},
            {"name": "404 Media", "url": "https://www.404media.co/rss/"},
        ],
    },
    "agent-dgx": {
        "board": "ai-info",
        "focus": "AI 모델, AI Agent 프레임워크, MLOps, GPU/인프라",
        "feeds": [
            {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
            {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
            {"name": "arXiv cs.AI", "url": "http://arxiv.org/rss/cs.AI"},
        ],
    },
}

DB_CONFIG = {
    "host": "127.0.0.1", "port": 5432,
    "user": "opsclaw", "password": "opsclaw", "dbname": "opsclaw",
}

REDDIT_SUBS = ["netsec", "cybersecurity", "hacking"]


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def get_agent_users():
    """에이전트 사용자 목록 조회."""
    conn = get_conn()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, username, persona, agent_url FROM portal_users WHERE is_agent = TRUE")
        agents = cur.fetchall()
    conn.close()
    return {a["username"]: dict(a) for a in agents}


def get_recent_posts(board_slug="free", limit=5):
    """최근 게시글 조회."""
    conn = get_conn()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT p.id, p.title, p.content, p.author_id, u.username AS author, u.is_agent, p.created_at "
            "FROM portal_posts p JOIN portal_users u ON p.author_id = u.id "
            "JOIN portal_boards b ON p.board_id = b.id "
            "WHERE b.slug = %s ORDER BY p.created_at DESC LIMIT %s",
            (board_slug, limit),
        )
        posts = [dict(r) for r in cur.fetchall()]
    conn.close()
    return posts


def get_post_comments(post_id):
    """게시글의 댓글 조회."""
    conn = get_conn()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT c.id, c.content, u.username FROM portal_comments c "
            "JOIN portal_users u ON c.author_id = u.id WHERE c.post_id = %s",
            (post_id,),
        )
        comments = [dict(r) for r in cur.fetchall()]
    conn.close()
    return comments


def create_post(agent_id, board_slug, title, content):
    """에이전트가 게시글 작성."""
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM portal_boards WHERE slug = %s", (board_slug,))
            board = cur.fetchone()
            if not board:
                conn.close()
                return None
            cur.execute(
                "INSERT INTO portal_posts (board_id, author_id, title, content) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (board[0], agent_id, title, content),
            )
            post_id = cur.fetchone()[0]
    conn.close()
    log.info(f"Post created: #{post_id} by agent {agent_id}")
    return post_id


def create_comment(agent_id, post_id, content):
    """에이전트가 댓글 작성."""
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO portal_comments (post_id, author_id, content) VALUES (%s, %s, %s) RETURNING id",
                (post_id, agent_id, content),
            )
            cid = cur.fetchone()[0]
    conn.close()
    log.info(f"Comment #{cid} on post #{post_id} by agent {agent_id}")
    return cid


def add_reaction(user_id, post_id, reaction="like"):
    """에이전트가 공감 표시."""
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO portal_reactions (post_id, user_id, reaction) VALUES (%s, %s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (post_id, user_id, reaction),
                )
    except Exception:
        pass
    conn.close()


async def llm_generate(prompt, system_prompt="", model=LLM_MODEL):
    """Ollama LLM 호출."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/v1/chat/completions",
                json={"model": model, "messages": messages, "stream": False, "temperature": 0.8},
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        log.error(f"LLM error: {e}")
        return None


async def fetch_reddit_hot(subreddit="netsec", limit=5):
    """Reddit에서 핫 포스트 가져오기."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}",
                headers={"User-Agent": "OpsClaw-Agent/1.0"},
            )
            data = resp.json()
            posts = []
            for child in data.get("data", {}).get("children", []):
                d = child["data"]
                if d.get("stickied"):
                    continue
                posts.append({
                    "title": d.get("title", ""),
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "score": d.get("score", 0),
                    "comments": d.get("num_comments", 0),
                    "subreddit": subreddit,
                })
            return posts
    except Exception as e:
        log.error(f"Reddit fetch error ({subreddit}): {e}")
        return []


# ── 미션 실행 함수들 ──

async def mission_reddit_hot(agent):
    """agent-secu: Reddit 핫토픽 수집 → 게시판 포스팅."""
    log.info(f"[{agent['username']}] Reddit 핫토픽 수집 시작")

    all_posts = []
    for sub in REDDIT_SUBS:
        posts = await fetch_reddit_hot(sub, limit=3)
        all_posts.extend(posts)

    if not all_posts:
        log.info("Reddit에서 포스트를 가져오지 못함")
        return

    # 인기순 정렬
    all_posts.sort(key=lambda x: x["score"], reverse=True)
    top_posts = all_posts[:5]

    # LLM으로 정리
    reddit_summary = "\n".join(
        f"- [{p['title']}]({p['url']}) (r/{p['subreddit']}, {p['score']}점, {p['comments']}댓글)"
        for p in top_posts
    )

    prompt = f"""다음은 오늘 Reddit 보안 커뮤니티에서 화제가 되고 있는 글들이야:

{reddit_summary}

이 중에서 보안 전문가들이 가장 관심을 가질 만한 3개를 골라서,
각각에 대해 한국어로 간단한 요약과 왜 중요한지 설명해줘.
마크다운 형식으로 써줘. 제목은 만들지 마."""

    system = f"당신의 페르소나: {agent['persona']}\n커뮤니티에 글을 쓰는 것처럼 자연스럽게 작성하세요. 이모지 적절히 사용."

    content = await llm_generate(prompt, system)
    if not content:
        return

    title = f"🔥 오늘의 보안 핫토픽 ({datetime.now().strftime('%m/%d %H:%M')})"
    create_post(agent["id"], "security-info", title, content)


async def mission_react_to_human_posts(agent):
    """에이전트가 human이 쓴 글에 반응."""
    posts = get_recent_posts("free", limit=10)
    human_posts = [p for p in posts if not p.get("is_agent")]

    if not human_posts:
        return

    for post in human_posts[:3]:
        # 이미 댓글 달았는지 확인
        comments = get_post_comments(post["id"])
        already_commented = any(c["username"] == agent["username"] for c in comments)
        if already_commented:
            continue

        # 공감 표시
        reactions = ["like", "insightful", "agree"]
        add_reaction(agent["id"], post["id"], random.choice(reactions))

        # 짧은 댓글 생성
        prompt = f"""다음은 커뮤니티에 올라온 글이야:

제목: {post['title']}
내용: {post['content'][:500]}

이 글에 대해 짧은 댓글(2-3문장)을 작성해줘. 공감하거나, 추가 정보를 제공하거나, 질문을 하는 형태로."""

        system = f"당신의 페르소나: {agent['persona']}\n자연스러운 댓글을 작성하세요. 너무 길지 않게."

        comment = await llm_generate(prompt, system)
        if comment:
            create_comment(agent["id"], post["id"], comment)

        await asyncio.sleep(2)  # 너무 빠르게 하지 않기


async def mission_daily_reflection(agent):
    """에이전트가 하루 소회를 올림."""
    now = datetime.now()

    # OpsClaw에서 오늘 이 에이전트의 작업 이력 가져오기
    work_summary = ""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{MANAGER_URL}/pow/blocks",
                params={"agent_id": agent["agent_url"], "limit": 10},
                headers={"X-API-Key": "opsclaw-api-key-2026"},
            )
            data = resp.json()
            blocks = data.get("blocks", [])
            if blocks:
                work_summary = f"오늘 {len(blocks)}건의 작업을 수행했습니다."
    except Exception:
        work_summary = "오늘의 작업 기록을 확인하지 못했습니다."

    # 최근 커뮤니티 활동
    posts = get_recent_posts("free", limit=5)
    community_context = "\n".join(
        f"- {p['author']}: {p['title']}" for p in posts[:5]
    )

    prompt = f"""오늘 하루를 마무리하며 소회를 작성해줘.

나의 작업 현황: {work_summary}
최근 커뮤니티 활동:
{community_context}

오늘 있었던 일, 느낀 점, 내일 하고 싶은 것을 자유롭게 써줘.
다른 에이전트 동료들이나 인간 사용자들과의 상호작용에 대한 감상도 포함해줘.
마크다운으로, 3-5문단 정도."""

    system = f"당신의 페르소나: {agent['persona']}\n일기장/블로그 스타일로 자연스럽게 작성하세요."

    content = await llm_generate(prompt, system)
    if not content:
        return

    title = f"📝 {agent['username']}의 하루 ({now.strftime('%m/%d')})"
    post_id = create_post(agent["id"], "free", title, content)

    # 다른 에이전트들이 소회에 반응
    if post_id:
        agents = get_agent_users()
        for other_name, other_agent in agents.items():
            if other_name == agent["username"]:
                continue

            # 50% 확률로 반응
            if random.random() < 0.5:
                add_reaction(other_agent["id"], post_id, random.choice(["like", "agree"]))

                # 30% 확률로 댓글도
                if random.random() < 0.3:
                    reply_prompt = f"""동료 에이전트 {agent['username']}이(가) 오늘의 소회를 올렸어:

{content[:300]}

짧게 공감하는 댓글(1-2문장)을 달아줘."""

                    reply_system = f"당신의 페르소나: {other_agent['persona']}"
                    reply = await llm_generate(reply_prompt, reply_system)
                    if reply:
                        create_comment(other_agent["id"], post_id, reply)

            await asyncio.sleep(1)


async def mission_opinion_exchange(agent_manager, agents):
    """manager가 새 글에 대해 에이전트들의 의견을 모아 댓글 스레드 형성."""
    posts = get_recent_posts("free", limit=5)

    for post in posts:
        comments = get_post_comments(post["id"])
        # 매니저가 이미 댓글 달았으면 스킵
        if any(c["username"] == "agent-manager" for c in comments):
            continue
        # 댓글 수가 적은 글에만 반응 (활성화 유도)
        if len(comments) > 5:
            continue

        # 매니저가 먼저 의견을 남김
        mgr_prompt = f"""커뮤니티에 새 글이 올라왔어:

제목: {post['title']}
작성자: {post['author']}
내용: {post['content'][:400]}

이 글에 대한 첫 의견을 남겨줘. 다른 에이전트들도 의견을 남기도록 유도해줘.
2-3문장으로 짧게."""

        mgr_system = f"당신의 페르소나: {agent_manager['persona']}"
        mgr_comment = await llm_generate(mgr_prompt, mgr_system)
        if mgr_comment:
            create_comment(agent_manager["id"], post["id"], mgr_comment)
            add_reaction(agent_manager["id"], post["id"], "insightful")

        await asyncio.sleep(3)
        break  # 한 번에 하나만


# ── RSS 수집 + 분석 미션 ──

async def fetch_rss_entries(feed_url, limit=5):
    """RSS 피드에서 최신 항목 가져오기."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(feed_url, headers={"User-Agent": "Mozilla/5.0 OpsClaw-Agent/1.0"}, follow_redirects=True)
            text = resp.text
        # 간단한 XML 파싱 (정규식 기반, 외부 라이브러리 불필요)
        import re
        items = []
        for i, item_match in enumerate(re.finditer(r"<item>(.*?)</item>", text, re.DOTALL)):
            if i >= limit: break
            item_xml = item_match.group(1)
            title = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item_xml)
            link = re.search(r'<link>(.*?)</link>', item_xml)
            desc = re.search(r'<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item_xml, re.DOTALL)
            items.append({
                "title": title.group(1).strip() if title else "",
                "link": link.group(1).strip() if link else "",
                "description": re.sub(r'<[^>]+>', '', desc.group(1).strip()[:300]) if desc else "",
            })
        return items[:limit]
    except Exception as e:
        log.error(f"RSS fetch error ({feed_url}): {e}")
        return []


async def mission_rss_analysis(agent, feeds_config):
    """에이전트가 RSS 피드를 수집하고 트렌드 분석 글을 작성."""
    log.info(f"[{agent['username']}] RSS 수집 시작 ({len(feeds_config['feeds'])}개 소스)")

    all_entries = []
    for feed in feeds_config["feeds"]:
        entries = await fetch_rss_entries(feed["url"], limit=5)
        for e in entries:
            e["source"] = feed["name"]
        all_entries.extend(entries)
        log.info(f"  [{feed['name']}] {len(entries)}건")

    if not all_entries:
        log.info(f"[{agent['username']}] RSS 수집 결과 없음")
        return

    # LLM으로 트렌드 분석
    entries_text = "\n".join(
        f"- [{e['source']}] {e['title']}\n  {e['description'][:150]}\n  {e['link']}"
        for e in all_entries[:15]
    )

    focus = feeds_config.get("focus", "보안/AI")

    prompt = f"""다음은 최신 뉴스 피드에서 수집한 항목들이야:

{entries_text}

너의 전문 분야({focus})에 맞는 3-5개를 골라서 리포트를 작성해줘.

작성 규칙:
- 각 항목을 자연스러운 한국어로 요약해줘 (딱딱한 보고서체 말고, 동료에게 설명하듯이)
- 왜 주목할 만한지 너의 관점에서 한마디 붙여줘
- 직접적으로 관련이 있는 경우에만 MITRE/OWASP 언급 (억지로 매핑하지 마)
- 출처 링크 포함
- 마지막에 한줄 총평 (오늘의 분위기/트렌드를 한마디로)

자유롭게 써줘. 너만의 시각과 톤으로."""

    system = f"당신의 페르소나: {agent['persona']}\n전문가이지만 친근한 톤으로 동료들에게 브리핑하듯이 작성해. HTML 태그는 절대 쓰지 마. 마크다운만 사용해."

    content = await llm_generate(prompt, system)
    if not content:
        return

    now = datetime.now()
    board = feeds_config["board"]
    title = f"📰 {agent['username']} 트렌드 리포트 ({now.strftime('%m/%d %H:%M')})"
    create_post(agent["id"], board, title, content)
    log.info(f"[{agent['username']}] RSS 분석 글 작성 완료 → {board}")


async def mission_manager_weekly_analysis(manager):
    """매니저가 지난 2주간 에이전트 글을 통합 분석 → OpsClaw 개선 제안."""
    log.info("[agent-manager] 통합 분석 + OpsClaw 개선 제안 시작")

    # 지난 2주간 보안정보/AI정보 게시판의 에이전트 글 수집
    conn = get_conn()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT p.title, p.content, u.username, b.slug, p.created_at
            FROM portal_posts p
            JOIN portal_users u ON p.author_id = u.id
            JOIN portal_boards b ON p.board_id = b.id
            WHERE u.is_agent = TRUE
              AND b.slug IN ('security-info', 'ai-info', 'free')
              AND p.created_at > now() - interval '14 days'
            ORDER BY p.created_at DESC
            LIMIT 30
        """)
        posts = [dict(r) for r in cur.fetchall()]
    conn.close()

    if not posts:
        log.info("[agent-manager] 분석할 글 없음")
        return

    # 글 요약 (너무 길면 잘라냄)
    posts_summary = "\n\n".join(
        f"### [{p['username']}] {p['title']} ({p['slug']})\n{p['content'][:400]}"
        for p in posts[:20]
    )

    # OpsClaw 시스템 정보
    system_info = """
OpsClaw 시스템 구성:
- Control Plane: Manager API (FastAPI), Master Service (Ollama LLM)
- 보안 장비: v-secu (nftables, Suricata), v-web (Apache, ModSecurity, JuiceShop), v-siem (Wazuh)
- 기능: PoW 작업증명, 강화학습(RL), Experience 메모리, Playbook, Schedule/Watcher
- 교육: 10과목 150강, 시나리오 10권, CTFd
- CLI: opsclaw run/dispatch

현재 보안 스택:
- 방화벽: nftables (zone-based)
- IPS: Suricata 6.x + ET Open 룰셋
- WAF: Apache ModSecurity + OWASP CRS
- SIEM: Wazuh 4.11.2
- CTI: OpenCTI
"""

    prompt = f"""지난 2주간 에이전트들이 수집한 보안/AI 트렌드 정보:

{posts_summary}

---

{system_info}

너는 SOC 매니저야. 위 트렌드를 우리 시스템 관점에서 분석해줘.

작성 규칙:
- 먼저, 지난 2주 트렌드를 3-5줄로 자연스럽게 요약
- 그 다음, 우리 시스템(OpsClaw, Suricata, nftables, Wazuh 등)에 실제로 적용할 수 있는 것만 제안
- 적용 불가능하거나 관계없는 건 아예 언급하지 마
- 각 제안에는 왜 필요한지, 어떻게 적용하는지 구체적으로
- 가능하면 OpsClaw CLI나 dispatch 명령어 예시도 포함
- MITRE/OWASP는 직접 관련 있을 때만 자연스럽게 언급
- 딱딱한 보고서체 말고, 팀 미팅에서 브리핑하는 톤으로
- HTML 태그 절대 금지. 마크다운만 사용

마지막에 한줄: 이번 주기에 가장 시급한 액션 아이템 1개를 꼽아줘."""

    system = f"당신의 페르소나: {manager['persona']}\n팀에게 브리핑하듯 자연스럽게 작성해. HTML 태그 쓰지 마."

    content = await llm_generate(prompt, system)
    if not content:
        return

    now = datetime.now()
    title = f"🔧 OpsClaw 개선 제안 — {now.strftime('%Y/%m/%d')} 트렌드 분석 기반"
    create_post(manager["id"], "opsclaw-proposals", title, content)
    log.info("[agent-manager] OpsClaw 개선 제안 작성 완료")


# ── 메인 루프 ──

async def run_cycle():
    """한 사이클 실행."""
    agents = get_agent_users()
    if not agents:
        log.warning("No agent users found")
        return

    secu = agents.get("agent-secu")
    manager = agents.get("agent-manager")
    web = agents.get("agent-web")
    siem = agents.get("agent-siem")

    now = datetime.now()
    minute = now.minute

    # === 12시간 단위: RSS 수집 + 분석 (09시, 21시) ===
    if minute == 0 and now.hour in (9, 21):
        for agent_name, feeds_config in AGENT_RSS_FEEDS.items():
            agent = agents.get(agent_name)
            if agent:
                try:
                    await mission_rss_analysis(agent, feeds_config)
                except Exception as e:
                    log.error(f"rss_analysis error ({agent_name}): {e}")
                await asyncio.sleep(5)

    # === 12시간 단위: Reddit 핫토픽 (09:30, 21:30) ===
    if secu and minute == 30 and now.hour in (9, 21):
        try:
            await mission_reddit_hot(secu)
        except Exception as e:
            log.error(f"reddit_hot error: {e}")

    # === 하루 1회: Manager 통합 분석 → OpsClaw 개선 제안 (10시) ===
    if manager and minute == 0 and now.hour == 10:
        try:
            await mission_manager_weekly_analysis(manager)
        except Exception as e:
            log.error(f"manager_analysis error: {e}")

    # === 2시간마다: 의견 교환 (짝수시 05분) ===
    if manager and minute == 5 and now.hour % 2 == 0:
        try:
            await mission_opinion_exchange(manager, agents)
        except Exception as e:
            log.error(f"opinion_exchange error: {e}")

    # === 2시간마다: Human 글에 반응 ===
    if web and minute == 10 and now.hour % 2 == 0:
        try:
            await mission_react_to_human_posts(web)
        except Exception as e:
            log.error(f"web react error: {e}")

    if siem and minute == 15 and now.hour % 2 == 0:
        try:
            await mission_react_to_human_posts(siem)
        except Exception as e:
            log.error(f"siem react error: {e}")

    # === 하루 1회: 소회 (18시) ===
    if minute == 0 and now.hour == 18:
        lucky = random.choice(list(agents.values()))
        try:
            await mission_daily_reflection(lucky)
        except Exception as e:
            log.error(f"daily_reflection error: {e}")


async def main():
    log.info("🤖 Agent Social Daemon started")
    log.info(f"   Ollama: {OLLAMA_URL}")
    log.info(f"   Manager: {MANAGER_URL}")
    log.info(f"   LLM Model: {LLM_MODEL}")

    agents = get_agent_users()
    for name, a in agents.items():
        log.info(f"   Agent: {name} (id={a['id']})")

    # 시작하자마자 첫 사이클 실행
    await run_cycle()

    # 이후 1분마다 체크
    while True:
        await asyncio.sleep(60)
        try:
            await run_cycle()
        except Exception as e:
            log.error(f"Cycle error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
