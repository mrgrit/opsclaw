FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install poetry && poetry install --no-root
CMD ["poetry", "run", "uvicorn", "apps.manager_api.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
