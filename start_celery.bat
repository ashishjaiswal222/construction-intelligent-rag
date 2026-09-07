@echo off
echo Ensuring Redis is running...
docker start redis-server >nul 2>&1 || docker run -d --name redis-server -p 6379:6379 redis:7-alpine >nul 2>&1

echo Starting Celery Worker...
start "Celery Worker" uv run celery -A core worker -l info -P eventlet -Q celery,llm_gemini_queue,llm_ollama_queue --concurrency=12

echo Starting Celery Beat...
start "Celery Beat" uv run celery -A core beat -l info

echo Celery has been started in separate windows!
