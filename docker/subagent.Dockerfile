FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install poetry && poetry install --no-root
CMD ["python", "apps/subagent_runtime/src/main.py"]
