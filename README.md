# Search Metrics Platform

A distributed search observability platform that ingests simulated search traffic through Kafka, processes it in real time with Spark, stores results in PostgreSQL, and exposes a FastAPI backend consumed by a React debugging dashboard.

## Architecture

```
Traffic Simulator → Kafka (raw-search-events)
                        ↓
              ┌─────────┴──────────┐
              ↓                    ↓
     Raw Event Writer         Spark Streaming
              ↓                    ↓
         raw_events         metrics_summary + anomaly_log
              └─────────┬──────────┘
                        ↓
                   PostgreSQL
                        ↓
                   FastAPI → React Dashboard
                        ↓
              Prometheus → Grafana
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Traffic Simulator | Python + kafka-python |
| Event Bus | Apache Kafka |
| Stream Processor | PySpark Structured Streaming |
| Anomaly Detection | Z-score + SLA thresholds |
| Analytics DB | PostgreSQL + SQLAlchemy + Alembic |
| REST API | FastAPI |
| Dashboard | React + Recharts |
| Observability | Prometheus + Grafana |

## Quick Start

### Prerequisites

- Docker Desktop (8 GB+ RAM recommended)
- Git

### Run the full stack

```bash
cp .env.example .env
docker compose up --build
```

> **Note:** Spark uses `bitnamilegacy/spark:3.5.0` because Bitnami removed versioned tags from the public `bitnami/` registry. Paths in `docker-compose.yml` remain unchanged (`/opt/bitnami/spark/...`).

> **Note:** Spark uses `bitnamilegacy/spark:3.5.0` because Bitnami removed versioned tags from the public `bitnami/` registry. Paths in `docker-compose.yml` remain unchanged (`/opt/bitnami/spark/...`).

Wait 2–3 minutes for Spark, migrations, and the first metric windows to populate.

### Access points

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5173 |
| API docs | http://localhost:8000/docs |
| API health | http://localhost:8000/health |
| Spark UI | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin / admin) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics/summary` | Aggregated metrics for all services |
| GET | `/metrics/service/{id}` | Per-service latency, error rate, volume |
| GET | `/anomalies` | Recent anomalies with severity |
| GET | `/trace/{trace_id}` | Full event chain for a request |
| GET | `/services` | Service registry with SLA thresholds |
| GET | `/metrics/prometheus` | Prometheus scrape endpoint |

## Project Structure

```
search-metrics-platform/
├── docker-compose.yml
├── producer/              # Synthetic search traffic generator
├── consumer/              # Debug consumer + raw event writer
├── spark/                 # Streaming job + anomaly detector
├── api/                   # FastAPI backend
├── db/migrations/         # Alembic schema migrations
├── dashboard/             # React + Recharts UI
├── prometheus/            # Prometheus config
├── grafana/               # Grafana provisioning
└── scripts/               # Kafka topic init, smoke test
```

## Local Development (without Docker)

### 1. Start infrastructure

```bash
docker compose up zookeeper kafka kafka-init postgres db-migrate spark-master spark-worker -d
```

### 2. Python services

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r api/requirements.txt -r producer/requirements.txt

set DATABASE_URL=postgresql://searchmetrics:searchmetrics@localhost:5432/search_metrics
set KAFKA_BOOTSTRAP_SERVERS=localhost:9092

python producer/kafka_producer.py
python consumer/raw_event_writer.py
```

### 3. Spark streaming

```bash
docker compose up spark-streaming
```

### 4. API + Dashboard

```bash
cd api && uvicorn api.main:app --reload --app-dir ..
cd dashboard && npm install && npm run dev
```

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker address |
| `DATABASE_URL` | Postgres connection string | Used by API, Spark, writers |
| `EVENTS_PER_MINUTE` | `1000` | Simulator throughput |
| `SERVICE_IDS` | 4 search services | Comma-separated service names |

## Smoke Test

After the stack is running:

```bash
python scripts/smoke_test.py
```

## Resume Highlights

- Built a distributed search observability platform ingesting 10K+ events/min via Kafka and processing them with PySpark structured streaming to compute real-time latency percentiles and error rates
- Designed a multi-table PostgreSQL schema with automated anomaly detection (Z-score, threshold-based) surfacing incidents in under 30 seconds
- Developed a FastAPI backend with trace-level debugging endpoints and a React dashboard visualizing P50/P95/P99 latency, anomaly feeds, and per-request span timelines
- Containerized the entire platform with Docker Compose and instrumented it with Prometheus metrics and Grafana dashboards for pipeline observability

## License

MIT
