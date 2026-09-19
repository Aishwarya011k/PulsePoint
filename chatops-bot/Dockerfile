FROM python:3.11-slim
WORKDIR /app
COPY chatops-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY chatops-bot/ .
CMD ["python", "bot.py"]
