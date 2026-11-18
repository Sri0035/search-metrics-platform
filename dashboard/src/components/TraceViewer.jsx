import { useEffect, useState } from "react";
import { getTrace } from "../api";

export default function TraceViewer({ traceId: externalTraceId }) {
  const [traceId, setTraceId] = useState(externalTraceId || "");
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (externalTraceId) {
      setTraceId(externalTraceId);
      lookupTrace(externalTraceId);
    }
  }, [externalTraceId]);

  async function lookupTrace(id = traceId) {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getTrace(id.trim());
      setEvents(data);
    } catch (err) {
      setEvents([]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2>Trace Viewer</h2>
      <form
        className="trace-form"
        onSubmit={(e) => {
          e.preventDefault();
          lookupTrace();
        }}
      >
        <input
          type="text"
          placeholder="Enter trace_id (UUID)"
          value={traceId}
          onChange={(e) => setTraceId(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "Lookup"}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {events.length === 0 && !error && !loading && (
        <p className="empty">Enter a trace ID to inspect request details.</p>
      )}

      <div className="trace-timeline">
        {events.map((event, index) => (
          <div
            key={`${event.trace_id}-${index}`}
            className={`trace-step ${event.status === "error" ? "error" : ""}`}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{event.service_id}</strong>
              <span>{new Date(event.ts).toLocaleTimeString()}</span>
            </div>
            <div style={{ marginTop: 4, color: "#94a3b8" }}>{event.query_text}</div>
            <div style={{ marginTop: 8, fontSize: "0.85rem" }}>
              Latency: {event.latency_ms}ms · Relevance: {event.relevance_score} · Status:{" "}
              {event.status}
              {event.error_code ? ` (${event.error_code})` : ""}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
