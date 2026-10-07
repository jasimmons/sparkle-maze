FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY server.py ./
COPY web web
COPY backend backend

EXPOSE 8000
# --proxy-headers so the OAuth callback URL comes out right behind a reverse proxy later.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
