FROM python:3.12-slim

RUN pip install --no-cache-dir uv

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --locked --no-cache --no-install-project

COPY app/ ./app/
RUN uv sync --locked --no-cache

ENV PATH="/app/.venv/bin:${PATH}"

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]