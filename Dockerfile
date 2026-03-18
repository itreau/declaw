FROM python:3.9-slim

LABEL maintainer="PyAgent"
LABEL description="Slack bot with LangChain orchestration for Ollama and OpenCode"

RUN useradd -m -u 1000 pyagent

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY agent.py .

RUN mkdir -p /app/output && chown -R pyagent:pyagent /app

USER pyagent

CMD ["python", "agent.py"]
