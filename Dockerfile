FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.7.10 /uv /uvx /bin/

WORKDIR /app


COPY pyproject.toml .
COPY uv.lock .

RUN uv sync

COPY . .

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
