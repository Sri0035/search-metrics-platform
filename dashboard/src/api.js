const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchJson(path) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${path}`);
  }
  return response.json();
}

export function getMetricsSummary(minutes = 60) {
  return fetchJson(`/metrics/summary?minutes=${minutes}`);
}

export function getServiceMetrics(serviceId, minutes = 60) {
  return fetchJson(`/metrics/service/${serviceId}?minutes=${minutes}`);
}

export function getAnomalies(hours = 24) {
  return fetchJson(`/anomalies?hours=${hours}`);
}

export function getTrace(traceId) {
  return fetchJson(`/trace/${traceId}`);
}

export function getServices() {
  return fetchJson("/services");
}
