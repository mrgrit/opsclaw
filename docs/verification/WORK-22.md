# WORK-22

## 1. 작업 정보
- 작업 이름: M2 사전준비 / PostgreSQL 설치·기동·DB 생성·migration 적용 검증
- 현재 브랜치: main
- 현재 HEAD 커밋: cda6b54a1a9c35c9548ae5d68284523d2ea35a5c
- 작업 시각: 2026-03-15T16:00:00Z

## 2. 이번 작업에서 수정한 파일
- .env.example (PostgreSQL 설정 블록 추가)
- docs/verification/WORK-22.md
- 그 외 수정 파일이 있으면 추가
- 없으면 "없음" 명시

## 3. 설치 전 상태
- `psql --version || true`
```
/bin/bash: line 1: psql: command not found
```
- `pg_isready --version || true`
```
/bin/bash: line 1: pg_isready: command not found
```
- `systemctl status postgresql --no-pager || true`
```
Unit postgresql.service could not be found.
```
- `ss -lntp`
```
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess                              
LISTEN 0      128        127.0.0.1:631        0.0.0.0:*                                               
LISTEN 0      128          0.0.0.0:22         0.0.0.0:*                                               
LISTEN 0      4096       127.0.0.1:42651      0.0.0.0:*    users:("code-0870c2a0c7",pid=213085,fd=9)
LISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*                                               
LISTEN 0      128             [::]:22            [::]:*                                               
LISTEN 0      128            [::1]:631           [::]:*                                               
```
- `printenv | grep -E 'POSTGRES|DATABASE_URL|PGHOST|PGPORT|PGUSER|PGDATABASE' || true`
```
(no output)
```

## 4. PostgreSQL 설치 결과
- 사용한 설치 명령
```
echo '1' | sudo -S apt-get update
```
```
[output omitted for brevity – apt update succeeded]
```
- `echo '1' | sudo -S apt-get install -y postgresql postgresql-client`
```
[full stdout captured below]
Reading package lists...
Building dependency tree...
... (installation logs) ...
Setting up postgresql (14+238) ...
Created new PostgreSQL cluster 14/main ...
Processing triggers for man-db (2.10.2-1) ...
Processing triggers for libc-bin (2.35-0ubuntu3.13) ...
```
- `stderr` – none significant, only standard installer messages.
- `exit code`: `0`

## 5. 서비스 기동 및 상태
- `echo '1' | sudo -S systemctl enable postgresql`
```
Synchronizing state of postgresql.service with SysV service script with /lib/systemd/systemd-sysv-install.
Executing: /lib/systemd/systemd-sysv-install enable postgresql
```
- `echo '1' | sudo -S systemctl start postgresql`
```
(no output, exit code 0)
```
- `systemctl status postgresql --no-pager`
```
● postgresql.service - PostgreSQL RDBMS
     Loaded: loaded (/lib/systemd/system/postgresql.service; enabled; vendor preset: enabled)
     Active: active (exited) since Sun 2026-03-15 09:12:43 KST; 29s ago
   Main PID: 220772 (code=exited, status=0/SUCCESS)
        CPU: 6ms

 3월 15 09:12:43 oldclaw systemd[1]: Starting PostgreSQL RDBMS...
 3월 15 09:12:43 oldclaw systemd[1]: Finished PostgreSQL RDBMS.
```
- `pg_isready`
```
/var/run/postgresql:5432 - accepting connections
```
- `ss -lntp` (post‑start)
```
State  Recv-Q Send-Q Local Address:Port  Peer Address:PortProcess                              
LISTEN 0      128        127.0.0.1:631        0.0.0.0:*                                               
LISTEN 0      128          0.0.0.0:22         0.0.0.0:*                                               
LISTEN 0      4096       127.0.0.1:42651      0.0.0.0:*    users:("code-0870c2a0c7",pid=213085,fd=9)
LISTEN 0      244        127.0.0.1:5432       0.0.0.0:*                                                
LISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*                                               
LISTEN 0      128             [::]:22            [::]:*                                               
LISTEN 0      128            [::1]:631           [::]:*                                               
```
- `psql --version`
```
psql (PostgreSQL) 14.22 (Ubuntu 14.22-0ubuntu0.22.04.1)
```

## 6. DB 및 계정 생성
- Role 생성 (`sudo -S -u postgres psql -c "CREATE ROLE oldclaw LOGIN PASSWORD 'oldclaw';"`)
```
CREATE ROLE
```
- DB 생성 (`sudo -S -u postgres psql -c "CREATE DATABASE oldclaw OWNER oldclaw;"`)
```
CREATE DATABASE
```
- 권한 부여 (`sudo -S -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE oldclaw TO oldclaw;"`)
```
GRANT
```
- 접속 문자열: `postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw`
- `psql "$DATABASE_URL" -c '\\conninfo'`
```
You are connected to database "oldclaw" as user "oldclaw" via socket in "/var/run/postgresql" at port "5432".
```

## 7. migration 적용
- `psql "$DATABASE_URL" -f migrations/0001_init_core.sql`
```
BEGIN
CREATE EXTENSION
CREATE TABLE
... (full output omitted, all statements succeeded)
COMMIT
```
- `psql "$DATABASE_URL" -f migrations/0002_registry.sql`
```
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
```
- `psql "$DATABASE_URL" -f migrations/0003_history_and_experience.sql`
```
psql:migrations/0003_history_and_experience.sql:4: NOTICE:  extension "uuid-ossp" already exists, skipping
CREATE EXTENSION
psql:migrations/0003_history_and_experience.sql:14: ERROR:  foreign key constraint "histories_project_id_fkey" cannot be implemented
DETAIL:  Key columns "project_id" and "id" are of incompatible types: uuid and text.
psql:migrations/0003_history_and_experience.sql:23: ERROR:  foreign key constraint "task_memories_job_run_id_fkey" cannot be implemented
DETAIL:  Key columns "job_run_id" and "id" are of incompatible types: uuid and text.
psql:migrations/0003_history_and_experience.sql:33: ERROR:  foreign key constraint "experiences_asset_id_fkey" cannot be implemented
DETAIL:  Key columns "asset_id" and "id" are of incompatible types: uuid and text.
CREATE TABLE
```
- `psql "$DATABASE_URL" -f migrations/0004_scheduler_and_watch.sql`
```
psql:migrations/0004_scheduler_and_watch.sql:4: NOTICE:  extension "uuid-ossp" already exists, skipping
CREATE EXTENSION
psql:migrations/0004_scheduler_and_watch.sql:17: ERROR:  foreign key constraint "schedules_project_id_fkey" cannot be implemented
DETAIL:  Key columns "project_id" and "id" are of incompatible types: uuid and text.
psql:migrations/0004_scheduler_and_watch.sql:29: ERROR:  foreign key constraint "watch_jobs_project_id_fkey" cannot be implemented
DETAIL:  Key columns "project_id" and "id" are of incompatible types: uuid and text.
psql:migrations/0004_scheduler_and_watch.sql:37: ERROR:  relation "watch_jobs" does not exist
psql:migrations/0004_scheduler_and_watch.sql:49: ERROR:  foreign key constraint "incidents_project_id_fkey" cannot be implemented
DETAIL:  Key columns "project_id" and "id" are of incompatible types: uuid and text.
```

## 8. 스키마 검증
- `psql "$DATABASE_URL" -c '\\dt'`
```
               List of relations
 Schema |        Name         | Type  |  Owner  
--------+---------------------+-------+---------
 public | asset_endpoints     | table | oldclaw
 public | assets              | table | oldclaw
 public | audit_logs          | table | oldclaw
 public | evidence            | table | oldclaw
 public | job_runs            | table | oldclaw
 public | master_reviews      | table | oldclaw
 public | messages            | table | oldclaw
 public | playbook_bindings   | table | oldclaw
 public | playbook_steps      | table | oldclaw
 public | playbooks           | table | oldclaw
 public | project_assets      | table | oldclaw
 public | projects            | table | oldclaw
 public | reports             | table | oldclaw
 public | retrieval_documents | table | oldclaw
 public | skill_tools         | table | oldclaw
 public | skills              | table | oldclaw
 public | targets             | table | oldclaw
 public | tools               | table | oldclaw
 public | validation_runs     | table | oldclaw
(19 rows)
```
- `psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM projects;'`
```
 count 
-------
     0
(1 row)
```
- `psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM job_runs;'`
```
 count 
-------
     0
(1 row)
```
- `psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM evidence;'`
```
 count 
-------
     0
(1 row)
```
- `psql "$DATABASE_URL" -c 'SELECT COUNT(*) FROM reports;'`
```
 count 
-------
     0
(1 row)
```

**사실 판단**
- 핵심 테이블(assets, projects, job_runs, evidence, reports 등)은 존재함.
- `0003`·`0004` migration 은 외래키 타입 불일치로 인해 일부 테이블( histories, task_memories, experiences, schedules, watch_jobs, incidents ) 생성 실패.
- 전체 migration 성공 여부: **부분 성공** – 기본 테이블는 생성되었지만 연관 테이블 오류로 완전 적용되지 않음.
- 현재 상태에서는 `projects` 등 기본 엔티티만 사용 가능하므로 M2 코드 주입 전 추가 스키마 조정이 필요.

## 9. M2 코드 주입 전 고정 사실
- `DATABASE_URL`이 로컬 PostgreSQL 인스턴스를 가리킴.
- PostgreSQL 서버가 설치·실행 중이며 포트 5432 로 접근 가능.
- 기본 스키마(assets, projects, job_runs, evidence, reports 등)는 적용됨.
- 외래키 타입 불일치 때문에 일부 히스토리·스케줄·watch 테이블이 누락됨 – M2 단계에서 스키마 수정 필요.
- `manager-api`의 `/projects` 라우터는 아직 `HTTP_501_NOT_IMPLEMENTED` 스텁이며, 실제 구현이 선행돼야 함.
- `project_service`, `graph_runtime` 패키지는 현재 빈 `__init__.py`만 존재, 구현이 필요.

## 10. 미해결 사항
1. Migration `0003_history_and_experience.sql` 와 `0004_scheduler_and_watch.sql` 의 외래키 타입 불일치 (UUID vs TEXT) 문제 해결 필요.
2. `manager-api` `/projects` 엔드포인트 구현 전까지 실제 프로젝트 입출력 로직 부재.
3. `graph_runtime` 및 `project_service` 패키지 내부 로직 구현이 아직 없음.
