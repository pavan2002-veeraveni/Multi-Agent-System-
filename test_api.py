"""Test API endpoints via FastAPI TestClient."""

import json
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

print("--> Testing GET /", flush=True)
r1 = client.get("/")
print("Status:", r1.status_code, flush=True)
print("Response:", json.dumps(r1.json(), indent=2), flush=True)

print("\n--> Testing GET /health", flush=True)
r2 = client.get("/health")
print("Status:", r2.status_code, "Response:", r2.json(), flush=True)

print("\n--> Testing POST /api/metrics/calculate", flush=True)
r3 = client.post("/api/metrics/calculate", json={"csv_path": "data/sample_metrics.csv"})
print("Status:", r3.status_code, flush=True)
print("Calculated columns:", r3.json()["statistics_markdown"][:150], "...", flush=True)

print("\n--> Testing POST /api/research", flush=True)
r4 = client.post(
    "/api/research",
    json={
        "query": "Tech Sector Q3 Analysis",
        "csv_path": "data/sample_metrics.csv",
        "mock": True,
    },
)
print("Status:", r4.status_code, flush=True)
data = r4.json()
print("Mode:", data.get("mode"), flush=True)
print("PDF output:", data["output_files"]["pdf_path"], flush=True)
print("Benchmarks:", json.dumps(data["benchmarks"]["summary"], indent=2), flush=True)

print("\n--> Testing GET /api/benchmarks", flush=True)
r5 = client.get("/api/benchmarks")
print("Status:", r5.status_code, flush=True)
print("Total routing events:", len(r5.json()["routing_history"]), flush=True)

print("\n--> Testing GET /api/reports/markdown", flush=True)
r6 = client.get("/api/reports/markdown")
print("Status:", r6.status_code, "| Content length:", len(r6.text), "chars", flush=True)

print("\n--> Testing GET /api/reports/download (PDF)", flush=True)
r7 = client.get("/api/reports/download")
print("Status:", r7.status_code, "| Content length:", len(r7.content), "bytes", flush=True)
print("PDF Magic Bytes:", r7.content[:5], flush=True)
