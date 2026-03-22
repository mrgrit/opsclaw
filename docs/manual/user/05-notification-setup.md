# 알림 채널 설정 가이드

OpsClaw는 Slack, Email, Webhook 3가지 알림 채널을 지원한다.

---

## 알림 채널 등록

### Slack

```bash
POST /notifications/channels
{
  "name": "slack-ops",
  "channel_type": "slack",
  "config": {
    "token": "xoxb-...",
    "channel": "#ops-alerts"
  }
}
```

`.env`에 기본값 설정 가능:
```env
SLACK_BOT_TOKEN=xoxb-...
```

### Email

```bash
POST /notifications/channels
{
  "name": "email-admin",
  "channel_type": "email",
  "config": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "admin@example.com",
    "password": "app-password",
    "from_addr": "admin@example.com",
    "to_addr": "team@example.com"
  }
}
```

### Webhook (HTTP POST)

```bash
POST /notifications/channels
{
  "name": "webhook-mattermost",
  "channel_type": "webhook",
  "config": {
    "url": "https://mattermost.internal/hooks/xxx",
    "method": "POST"
  }
}
```

---

## 알림 규칙 설정

이벤트가 발생할 때 어느 채널로 알림을 보낼지 규칙으로 정의한다.

```bash
POST /notifications/rules
{
  "name": "incident-to-slack",
  "event_type": "incident.created",   # 또는 * (모든 이벤트)
  "channel_id": "채널 ID",
  "enabled": true,
  "filter_conditions": {}              # 선택적 필터
}
```

---

## 지원 이벤트 타입

| event_type | 발생 시점 |
|-----------|---------|
| `incident.created` | Watch 모니터링에서 임계값 초과 시 |
| `schedule.failed` | 정기 스케줄 실행 실패 시 |
| `project.closed` | 프로젝트 종료 시 |
| `*` | 모든 이벤트 |

---

## 알림 이력 조회

```bash
GET /notifications/logs          # 전체 발송 이력
GET /notifications/channels      # 등록된 채널 목록
GET /notifications/rules         # 등록된 규칙 목록
```

---

## 테스트 발송

```bash
POST /notifications/test
{
  "channel_id": "채널 ID",
  "message": "OpsClaw 알림 테스트"
}
```

---

## 정기 스케줄 설정 (Schedule)

```bash
POST /schedules
{
  "name": "daily-health-check",
  "cron_expr": "0 9 * * *",       # 매일 오전 9시
  "project_template": {
    "name": "daily-health",
    "request_text": "서버 일일 현황 점검",
    "master_mode": "external"
  },
  "enabled": true
}
```

---

## 모니터링 Watch 설정

```bash
POST /watchers
{
  "name": "disk-watch",
  "check_command": "df -h / | awk 'NR==2{print $5}' | tr -d '%'",
  "threshold": 80,
  "interval_seconds": 300,
  "subagent_url": "http://localhost:8002"
}
```

임계값 초과 시 `incident.created` 이벤트 → 설정된 채널로 알림 발송.
