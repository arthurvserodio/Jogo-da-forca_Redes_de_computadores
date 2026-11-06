FROM ghcr.io/astral-sh/uv:0.11.24 AS uv
FROM python:3.13.12-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked
COPY . .
RUN uv run --locked python scripts/check.py
CMD ["uv", "run", "--locked", "python", "-m", "src.main"]
