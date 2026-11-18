CREATE TABLE IF NOT EXISTS service_registry (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) UNIQUE NOT NULL,
    owner_team VARCHAR(100) NOT NULL,
    sla_latency_ms INTEGER NOT NULL,
    sla_error_rate DOUBLE PRECISION NOT NULL
);

INSERT INTO service_registry (service_name, owner_team, sla_latency_ms, sla_error_rate)
VALUES
    ('search-api', 'Search Platform', 200, 0.02),
    ('recommendations', 'ML Team', 350, 0.03),
    ('indexer', 'Data Infra', 500, 0.01),
    ('ranking', 'Search Platform', 250, 0.025)
ON CONFLICT (service_name) DO NOTHING;
