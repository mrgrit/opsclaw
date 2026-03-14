# Makefile for OldClaw

.PHONY: install lint test run-manager run-master run-subagent

install:
	poetry install

lint:
	poetry run flake8 .

test:
	poetry run pytest -s -vv

run-manager:
	poetry run uvicorn apps.manager_api.src.main:app --reload

run-master:
	poetry run uvicorn apps.master_service.src.main:app --reload

run-subagent:
	python apps.subagent_runtime.src.main.py
