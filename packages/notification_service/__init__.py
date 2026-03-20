"""OpsClaw Notification Service — channel/rule CRUD + event firing + delivery logs."""

from __future__ import annotations

import os
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DB_URL)


# ── Channel CRUD ───────────────────────────────────────────────────────────────

def create_channel(
    name: str,
    channel_type: str,
    config: dict | None = None,
    enabled: bool = True,
    database_url: str | None = None,
) -> dict:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO notification_channels (name, channel_type, config, enabled)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (name, channel_type, Json(config or {}), enabled),
            )
            return dict(cur.fetchone())


def get_channel(channel_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM notification_channels WHERE id = %s", (channel_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_channel_by_name(name: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM notification_channels WHERE name = %s", (name,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_channels(enabled_only: bool = False, database_url: str | None = None) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if enabled_only:
                cur.execute(
                    "SELECT * FROM notification_channels WHERE enabled = true ORDER BY created_at"
                )
            else:
                cur.execute("SELECT * FROM notification_channels ORDER BY created_at")
            return [dict(r) for r in cur.fetchall()]


def update_channel(
    channel_id: str,
    *,
    enabled: bool | None = None,
    config: dict | None = None,
    database_url: str | None = None,
) -> dict:
    sets = []
    params: list[Any] = []
    if enabled is not None:
        sets.append("enabled = %s")
        params.append(enabled)
    if config is not None:
        sets.append("config = %s")
        params.append(Json(config))
    if not sets:
        row = get_channel(channel_id, database_url=database_url)
        if row is None:
            raise ValueError(f"Channel not found: {channel_id}")
        return row
    params.append(channel_id)
    sql = f"UPDATE notification_channels SET {', '.join(sets)} WHERE id = %s RETURNING *"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return dict(cur.fetchone())


def delete_channel(channel_id: str, database_url: str | None = None) -> bool:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notification_channels WHERE id = %s", (channel_id,))
            return cur.rowcount > 0


# ── Rule CRUD ─────────────────────────────────────────────────────────────────

def create_rule(
    name: str,
    event_type: str,
    channel_id: str,
    filter_conditions: dict | None = None,
    enabled: bool = True,
    database_url: str | None = None,
) -> dict:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO notification_rules (name, event_type, channel_id, filter_conditions, enabled)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (name, event_type, channel_id, Json(filter_conditions or {}), enabled),
            )
            return dict(cur.fetchone())


def get_rule(rule_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM notification_rules WHERE id = %s", (rule_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_rules(
    event_type: str | None = None,
    enabled_only: bool = True,
    database_url: str | None = None,
) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            conditions = []
            params: list[Any] = []
            if enabled_only:
                conditions.append("enabled = true")
            if event_type is not None:
                conditions.append("event_type = %s")
                params.append(event_type)
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            cur.execute(f"SELECT * FROM notification_rules {where} ORDER BY created_at", params)
            return [dict(r) for r in cur.fetchall()]


def update_rule(
    rule_id: str,
    *,
    enabled: bool | None = None,
    database_url: str | None = None,
) -> dict:
    if enabled is None:
        row = get_rule(rule_id, database_url=database_url)
        if row is None:
            raise ValueError(f"Rule not found: {rule_id}")
        return row
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE notification_rules SET enabled = %s WHERE id = %s RETURNING *",
                (enabled, rule_id),
            )
            return dict(cur.fetchone())


def delete_rule(rule_id: str, database_url: str | None = None) -> bool:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM notification_rules WHERE id = %s", (rule_id,))
            return cur.rowcount > 0


# ── Delivery ──────────────────────────────────────────────────────────────────

def _matches_filter(rule: dict, payload: dict) -> bool:
    """Return True if payload satisfies all filter_conditions."""
    conditions = rule.get("filter_conditions") or {}
    if not conditions:
        return True
    for key, value in conditions.items():
        if payload.get(key) != value:
            return False
    return True


def _send_to_channel(channel: dict, event_type: str, payload: dict) -> tuple[bool, str | None]:
    """Deliver to channel. Returns (success, error_message)."""
    channel_type = channel.get("channel_type", "log")
    config = channel.get("config") or {}

    if channel_type == "webhook":
        import urllib.request
        import urllib.error
        import json as _json

        url = config.get("url", "")
        if not url:
            return False, "webhook config missing 'url'"
        body = _json.dumps({
            "event_type": event_type,
            "payload": payload,
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            import socket
            with urllib.request.urlopen(req, timeout=5) as resp:
                status_code = resp.status
                if 200 <= status_code < 300:
                    return True, None
                return False, f"HTTP {status_code}"
        except urllib.error.HTTPError as exc:
            return False, f"HTTP {exc.code}: {exc.reason}"
        except (urllib.error.URLError, socket.timeout, OSError) as exc:
            return False, str(exc)

    elif channel_type == "email":
        import smtplib
        import json as _json
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = config.get("smtp_host", "")
        smtp_port = int(config.get("smtp_port", 587))
        username = config.get("username", "")
        password = config.get("password", "")
        from_addr = config.get("from_addr", username)
        to_addrs = config.get("to_addrs", [])
        use_tls = config.get("use_tls", True)
        subject_prefix = config.get("subject_prefix", "[OpsClaw]")

        if not smtp_host:
            return False, "email config missing 'smtp_host'"
        if not to_addrs:
            return False, "email config missing 'to_addrs'"

        subject = f"{subject_prefix} {event_type}"
        body = _json.dumps({"event_type": event_type, "payload": payload}, indent=2, ensure_ascii=False)

        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            if use_tls:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
                    smtp.starttls()
                    if username:
                        smtp.login(username, password)
                    smtp.sendmail(from_addr, to_addrs, msg.as_string())
            else:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as smtp:
                    if username:
                        smtp.login(username, password)
                    smtp.sendmail(from_addr, to_addrs, msg.as_string())
            return True, None
        except smtplib.SMTPException as exc:
            return False, str(exc)
        except OSError as exc:
            return False, str(exc)

    elif channel_type == "slack":
        import urllib.request
        import urllib.error
        import json as _json

        bot_token = config.get("bot_token", "")
        channel = config.get("channel", "")

        if not bot_token:
            return False, "slack config missing 'bot_token'"
        if not channel:
            return False, "slack config missing 'channel'"

        text = f"*[OpsClaw] {event_type}*\n```{_json.dumps(payload, indent=2, ensure_ascii=False)}```"
        body = _json.dumps({"channel": channel, "text": text}).encode("utf-8")
        req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bot_token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = _json.loads(resp.read().decode("utf-8"))
                if result.get("ok"):
                    return True, None
                return False, result.get("error", "slack api error")
        except (urllib.error.URLError, OSError) as exc:
            return False, str(exc)

    else:  # 'log' or unknown
        print(f"[notification_service] LOG: event={event_type} channel={channel.get('name')} payload={payload}")
        return True, None


def fire_event(
    event_type: str,
    payload: dict,
    database_url: str | None = None,
) -> list[dict]:
    """Match rules to event_type, deliver, and log results."""
    # Fetch matching rules: exact event_type match OR wildcard '*'
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT r.*, c.channel_type, c.config, c.name AS channel_name, c.enabled AS channel_enabled
                FROM notification_rules r
                JOIN notification_channels c ON c.id = r.channel_id
                WHERE r.enabled = true
                  AND c.enabled = true
                  AND (r.event_type = %s OR r.event_type = '*')
                ORDER BY r.created_at
                """,
                (event_type,),
            )
            rules = [dict(r) for r in cur.fetchall()]

    logs = []
    for rule in rules:
        if not _matches_filter(rule, payload):
            continue

        channel = {
            "id": str(rule["channel_id"]),
            "channel_type": rule["channel_type"],
            "config": rule["config"],
            "name": rule["channel_name"],
        }
        ok, err = _send_to_channel(channel, event_type, payload)
        log_status = "sent" if ok else "failed"

        with _conn(database_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO notification_logs
                        (rule_id, channel_id, event_type, payload, status, error)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        str(rule["id"]),
                        str(rule["channel_id"]),
                        event_type,
                        Json(payload),
                        log_status,
                        err,
                    ),
                )
                logs.append(dict(cur.fetchone()))

    return logs


def list_notification_logs(
    channel_id: str | None = None,
    event_type: str | None = None,
    limit: int = 50,
    database_url: str | None = None,
) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            conditions = []
            params: list[Any] = []
            if channel_id is not None:
                conditions.append("channel_id = %s")
                params.append(channel_id)
            if event_type is not None:
                conditions.append("event_type = %s")
                params.append(event_type)
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            params.append(limit)
            cur.execute(
                f"SELECT * FROM notification_logs {where} ORDER BY sent_at DESC LIMIT %s",
                params,
            )
            return [dict(r) for r in cur.fetchall()]
