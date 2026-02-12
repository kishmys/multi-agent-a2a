FROM python:3.12-slim

WORKDIR /app

COPY main.py .

RUN pip install fastapi uvicorn google-generativeai

EXPOSE 8080

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}