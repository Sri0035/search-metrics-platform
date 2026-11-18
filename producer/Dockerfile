FROM python:3.11-slim

WORKDIR /app

COPY producer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY producer/kafka_producer.py .

CMD ["python", "kafka_producer.py"]
