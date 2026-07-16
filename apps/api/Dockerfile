FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt requirements-semantic.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt -r requirements-semantic.txt

COPY alembic.ini main.py ./
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts

USER app
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
