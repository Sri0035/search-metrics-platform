import { useEffect, useState } from "react";
import { getAnomalies } from "../api";

export default function AnomalyFeed({ onSelectTrace }) {
  const [anomalies, setAnomalies] = useState([]);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getAnomalies(24);
        setAnomalies(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      }
    }
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <h2>Anomaly Feed</h2>
      {error && <div className="error">{error}</div>}

      {anomalies.length === 0 ? (
        <p className="empty">No anomalies detected yet.</p>
      ) : (
        <ul className="anomaly-list">
          {anomalies.map((item) => (
            <li
              key={item.id}
              className="anomaly-item"
              onClick={() => {
                setExpandedId(expandedId === item.id ? null : item.id);
                if (item.trace_id) onSelectTrace?.(item.trace_id);
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <strong>{item.service_id}</strong>
                <span className={`badge ${item.severity}`}>{item.severity}</span>
              </div>
              <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: 4 }}>
                {item.anomaly_type.replace(/_/g, " ")} ·{" "}
                {new Date(item.detected_at).toLocaleString()}
              </div>
              <div style={{ fontSize: "0.85rem", marginTop: 4 }}>
                Value: {item.metric_value.toFixed(3)} (threshold: {item.threshold.toFixed(3)})
              </div>
              {expandedId === item.id && item.trace_id && (
                <div style={{ marginTop: 8, color: "#60a5fa", fontSize: "0.8rem" }}>
                  trace: {item.trace_id}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
