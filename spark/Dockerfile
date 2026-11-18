# bitnami/spark tags were moved to bitnamilegacy (see Bitnami catalog changes 2025+)
FROM bitnamilegacy/spark:3.5.0

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY spark/requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY spark/ /app/
WORKDIR /app

USER root
RUN mkdir -p /tmp/spark-checkpoints && chmod 777 /tmp/spark-checkpoints

USER 1001
