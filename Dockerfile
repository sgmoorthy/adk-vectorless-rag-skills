FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
# Fallback installing standard dependencies if google-adk is private/mocked
RUN pip install --no-cache-dir -r requirements.txt || pip install fastapi uvicorn pydantic sqlalchemy asyncpg alembic 

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
