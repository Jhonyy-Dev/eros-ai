FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ server/
COPY motor/ motor/
COPY config/ config/
COPY datos/ datos/

ENV HOST=0.0.0.0
ENV PUERTO=7860
ENV PORT=7860
ENV BACKEND=openrouter
ENV FALLBACK_LOCAL=false
EXPOSE 7860

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
