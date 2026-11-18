import { useState } from "react";
import AnomalyFeed from "./components/AnomalyFeed";
import MetricsSummary from "./components/MetricsSummary";
import TraceViewer from "./components/TraceViewer";

export default function App() {
  const [selectedTraceId, setSelectedTraceId] = useState("");

  return (
    <div className="app">
      <header>
        <h1>Search Metrics Platform</h1>
        <p>Real-time search observability — latency, errors, anomalies, and trace debugging</p>
      </header>

      <div className="grid">
        <MetricsSummary />
        <div className="grid-2">
          <AnomalyFeed onSelectTrace={setSelectedTraceId} />
          <TraceViewer traceId={selectedTraceId} />
        </div>
      </div>
    </div>
  );
}
