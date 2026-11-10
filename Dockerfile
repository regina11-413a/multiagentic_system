FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main_agent.py .
COPY SOUL.md .
COPY ToR.md .
COPY skills/ ./skills/
CMD ["python", "main_agent.py"]
