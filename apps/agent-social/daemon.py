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
    create_post(agent["id"], "free", title, content)


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

    # 10분마다: Reddit 핫토픽 (agent-secu)
    if secu and minute == 0 and now.hour % 2 == 0:
        try:
            await mission_reddit_hot(secu)
        except Exception as e:
            log.error(f"reddit_hot error: {e}")

    # 15분마다: 의견 교환 (agent-manager)
    if manager and minute == 5 and now.hour % 2 == 0:
        try:
            await mission_opinion_exchange(manager, agents)
        except Exception as e:
            log.error(f"opinion_exchange error: {e}")

    # 5분마다: Human 글에 반응 (agent-web)
    if web and minute == 10 and now.hour % 2 == 0:
        try:
            await mission_react_to_human_posts(web)
        except Exception as e:
            log.error(f"web react error: {e}")

    # 8분마다: Human 글에 반응 (agent-siem)
    if siem and minute == 15 and now.hour % 2 == 0:
        try:
            await mission_react_to_human_posts(siem)
        except Exception as e:
            log.error(f"siem react error: {e}")

    # 매시 정각: 하루 소회 (랜덤 에이전트 1명)
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
