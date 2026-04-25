FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY docs/ ./docs/
COPY tests/mock_reverb.json ./tests/mock_reverb.json

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV USE_MOCK_REVERB=true

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
