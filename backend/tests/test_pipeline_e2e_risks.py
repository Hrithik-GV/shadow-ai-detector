import io
import pytest
from fastapi.testclient import TestClient

from app.main import app

USER_SAMPLE_CSV = """timestamp,source_ip,destination_ip,destination_domain,destination_port,protocol,bytes_sent,bytes_received
2026-10-10T09:00:00Z,192.168.1.10,104.18.33.45,example.com,443,TCP,1200,4500
2026-10-10T09:01:00Z,192.168.1.11,142.250.72.14,google.com,443,TCP,800,3200
2026-10-10T09:02:00Z,192.168.1.10,192.168.1.20,,8080,TCP,500,900
2026-10-10T09:05:00Z,192.168.1.10,104.18.33.45,api.openai.com,443,TCP,18500,72000
2026-10-10T09:06:00Z,192.168.1.11,160.79.104.10,api.anthropic.com,443,TCP,42000,86000
2026-10-10T09:07:00Z,192.168.1.12,142.250.72.14,generativelanguage.googleapis.com,443,TCP,26500,110000
2026-10-10T09:08:00Z,192.168.1.13,13.107.42.14,copilot.microsoft.com,443,TCP,15000,54000
2026-10-10T09:09:00Z,192.168.1.14,198.51.100.23,unverified-ai-test.invalid,443,TCP,63000,12000
2026-10-10T09:10:00Z,192.168.1.10,104.18.33.45,api.openai.com,443,TCP,51000,190000
2026-10-10T09:11:00Z,192.168.1.15,160.79.104.10,api.anthropic.com,443,TCP,78000,22000
"""


def test_user_csv_pipeline_e2e():
    """Trace the user's sample CSV through ingestion, detection, risk evaluation, and API retrieval."""
    client = TestClient(app)

    # Step 1: Upload and analyze CSV
    files = {"file": ("user_traffic.csv", io.BytesIO(USER_SAMPLE_CSV.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/traffic/analyze", files=files)
    assert upload_res.status_code == 201, upload_res.text
    data = upload_res.json()
    assert data["valid_rows"] == 10
    assert data["rejected_rows"] == 0

    # Step 2: Query AI Inventory
    inv_res = client.get("/api/inventory")
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert len(inv_data) >= 4

    discovered_domains = {item["domain"] for item in inv_data}
    assert "api.openai.com" in discovered_domains
    assert "api.anthropic.com" in discovered_domains
    assert "generativelanguage.googleapis.com" in discovered_domains
    assert "copilot.microsoft.com" in discovered_domains

    # Unknown domain must NOT be in AI inventory (handled as uncertain)
    assert "unverified-ai-test.invalid" not in discovered_domains
    assert "example.com" not in discovered_domains
    assert "google.com" not in discovered_domains

    # Check OpenAI approval (OpenAI is default approved)
    openai_item = next(i for i in inv_data if i["domain"] == "api.openai.com")
    assert openai_item["isApproved"] is True
    assert openai_item["approvalStatus"] == "approved"
    assert openai_item["totalCalls"] == 2

    # Check Anthropic unapproved shadow status
    anthropic_item = next(i for i in inv_data if i["domain"] == "api.anthropic.com")
    assert anthropic_item["isApproved"] is False
    assert anthropic_item["approvalStatus"] == "unapproved"
    assert anthropic_item["totalCalls"] == 2
    assert anthropic_item["riskLevel"] in ["high", "critical"]

    # Step 3: Query Risk Findings
    risks_res = client.get("/api/risks")
    assert risks_res.status_code == 200
    risks_data = risks_res.json()
    assert len(risks_data) >= 3

    risk_providers = {r["provider"] for r in risks_data}
    assert "Anthropic" in risk_providers
    assert "Google" in risk_providers
    assert "Microsoft" in risk_providers

    anthropic_finding = next(r for r in risks_data if r["provider"] == "Anthropic")
    assert anthropic_finding["isApproved"] is False
    assert anthropic_finding["riskLevel"] in ["high", "critical"]
    assert len(anthropic_finding["reasons"]) > 0
    assert len(anthropic_finding["evidence"]) > 0

    # Step 4: Query Dashboard Stats
    stats_res = client.get("/api/dashboard/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["aiRelatedRecords"] >= 6
    assert stats["totalAiEndpoints"] >= 4
    assert stats["unapprovedEndpointsCount"] >= 3
    assert stats["flaggedRiskCount"] >= 3

    # Step 5: Query Test Evaluation Metrics
    metrics_res = client.get("/api/reports/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["precision"] == 1.0
    assert metrics["falsePositiveRate"] == 0.0
