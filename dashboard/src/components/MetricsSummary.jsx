import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getMetricsSummary, getServices } from "../api";

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function gaugeClass(value, threshold) {
  if (value <= threshold) return "ok";
  if (value <= threshold * 1.5) return "warn";
  return "bad";
}

export default function MetricsSummary({ onSelectService }) {
  const [metrics, setMetrics] = useState([]);
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState("all");
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const [summary, registry] = await Promise.all([
          getMetricsSummary(60),
          getServices(),
        ]);
        setMetrics(summary.services || []);
        setServices(registry);
        setError(null);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const serviceIds = useMemo(() => {
    const ids = [...new Set(metrics.map((m) => m.service_id))];
    return ids.sort();
  }, [metrics]);

  const filtered = useMemo(() => {
    if (selectedService === "all") return metrics;
    return metrics.filter((m) => m.service_id === selectedService);
  }, [metrics, selectedService]);

  const latencyChartData = useMemo(() => {
    const byWindow = {};
    for (const row of filtered) {
      const key = row.window_start;
      if (!byWindow[key]) {
        byWindow[key] = { window: formatTime(key), window_start: key };
      }
      byWindow[key][`${row.service_id}_p95`] = row.p95_latency;
      byWindow[key][`${row.service_id}_p99`] = row.p99_latency;
    }
    return Object.values(byWindow).sort(
      (a, b) => new Date(a.window_start) - new Date(b.window_start)
    );
  }, [filtered]);

  const volumeChartData = useMemo(() => {
    const byWindow = {};
    for (const row of filtered) {
      const key = row.window_start;
      if (!byWindow[key]) {
        byWindow[key] = { window: formatTime(key) };
      }
      byWindow[key][row.service_id] = row.query_count;
    }
    return Object.values(byWindow);
  }, [filtered]);

  const latestByService = useMemo(() => {
    const latest = {};
    for (const row of metrics) {
      if (
        !latest[row.service_id] ||
        new Date(row.window_start) > new Date(latest[row.service_id].window_start)
      ) {
        latest[row.service_id] = row;
      }
    }
    return latest;
  }, [metrics]);

  const totalQueries = metrics.reduce((sum, m) => sum + m.query_count, 0);
  const avgError =
    metrics.length > 0
      ? metrics.reduce((sum, m) => sum + m.error_rate, 0) / metrics.length
      : 0;

  return (
    <div className="card">
      <h2>Metrics Summary</h2>
      {error && <div className="error">{error}</div>}

      <div className="stats-row">
        <div className="stat">
          <label>Total Queries (60m)</label>
          <value>{totalQueries.toLocaleString()}</value>
        </div>
        <div className="stat">
          <label>Avg Error Rate</label>
          <value>{(avgError * 100).toFixed(2)}%</value>
        </div>
        <div className="stat">
          <label>Services</label>
          <value>{serviceIds.length || services.length}</value>
        </div>
      </div>

      <div className="service-tabs">
        <button
          className={selectedService === "all" ? "active" : ""}
          onClick={() => setSelectedService("all")}
        >
          All
        </button>
        {serviceIds.map((id) => (
          <button
            key={id}
            className={selectedService === id ? "active" : ""}
            onClick={() => {
              setSelectedService(id);
              onSelectService?.(id);
            }}
          >
            {id}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="empty">Waiting for metrics data from the pipeline...</p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={latencyChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="window" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" unit="ms" />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #475569" }} />
              <Legend />
              {serviceIds.map((id, idx) => (
                <Line
                  key={`${id}-p95`}
                  type="monotone"
                  dataKey={`${id}_p95`}
                  name={`${id} P95`}
                  stroke={["#3b82f6", "#22c55e", "#eab308", "#a855f7"][idx % 4]}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>

          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={volumeChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="window" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #475569" }} />
              <Legend />
              {serviceIds.map((id, idx) => (
                <Bar
                  key={id}
                  dataKey={id}
                  fill={["#3b82f6", "#22c55e", "#eab308", "#a855f7"][idx % 4]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>

          <h3 style={{ marginTop: 24, color: "#cbd5e1" }}>Error Rate vs SLA</h3>
          {Object.entries(latestByService).map(([serviceId, row]) => {
            const sla = services.find((s) => s.service_name === serviceId);
            const threshold = sla?.sla_error_rate ?? 0.05;
            return (
              <div key={serviceId} className="gauge">
                <span style={{ minWidth: 120 }}>{serviceId}</span>
                <div className="gauge-bar">
                  <div
                    className={`gauge-fill ${gaugeClass(row.error_rate, threshold)}`}
                    style={{ width: `${Math.min(row.error_rate / threshold, 1) * 100}%` }}
                  />
                </div>
                <span>{(row.error_rate * 100).toFixed(2)}% / {(threshold * 100).toFixed(1)}%</span>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
