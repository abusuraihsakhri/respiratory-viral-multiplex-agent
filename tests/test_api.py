"""
Automated Pytest for Respiratory Viral Multiplex Agent API layer.
Tests input validation, PHI guard integration, and Prometheus metrics format.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from agents.api import app
from agents.base import PHIGuard, AuditLogger, SecurityException


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_healthy(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "HEALTHY"
        assert data["service"] == "respiratory-viral-multiplex-agent"


class TestPrometheusMetrics:
    def test_metrics_returns_text_format(self):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]

    def test_metrics_contains_required_series(self):
        resp = client.get("/metrics")
        body = resp.text
        assert "dossiers_processed_total" in body
        assert "audit_blocks_total" in body
        assert "system_status" in body
        assert "# HELP" in body
        assert "# TYPE" in body

    def test_metrics_type_declarations(self):
        resp = client.get("/metrics")
        body = resp.text
        assert "TYPE dossiers_processed_total counter" in body
        assert "TYPE audit_blocks_total counter" in body
        assert "TYPE system_status gauge" in body


class TestAuditEndpoint:
    def test_audit_valid_payload(self):
        payload = {
            "task_id": "API-TEST-001",
            "target_identifier": "SPECIMEN-API-01",
            "primary_metric": 15.0,
            "secondary_metric": 5.0,
            "status_descriptor": "NOMINAL",
            "is_critical_flag": False,
        }
        resp = client.post("/api/audit", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == "API-TEST-001"
        assert "overall_urgency" in data

    def test_audit_rejects_phi_in_task_id(self):
        payload = {
            "task_id": "Patient MRN-12345678",
            "target_identifier": "SPEC-01",
            "primary_metric": 10.0,
        }
        resp = client.post("/api/audit", json=payload)
        assert resp.status_code == 422

    def test_audit_rejects_phi_in_target(self):
        payload = {
            "task_id": "TASK-001",
            "target_identifier": "Patient John Doe record",
            "primary_metric": 10.0,
        }
        resp = client.post("/api/audit", json=payload)
        assert resp.status_code == 422

    def test_audit_rejects_oversized_metric(self):
        payload = {
            "task_id": "TASK-001",
            "target_identifier": "SPEC-01",
            "primary_metric": 1e10,
        }
        resp = client.post("/api/audit", json=payload)
        assert resp.status_code == 422

    def test_audit_rejects_empty_task_id(self):
        payload = {
            "task_id": "",
            "target_identifier": "SPEC-01",
            "primary_metric": 10.0,
        }
        resp = client.post("/api/audit", json=payload)
        assert resp.status_code == 422

    def test_audit_triggers_critical(self):
        payload = {
            "task_id": "API-CRIT-001",
            "target_identifier": "SPEC-CRIT-01",
            "primary_metric": 30.0,
            "secondary_metric": 15.0,
            "is_critical_flag": True,
            "status_descriptor": "DISCORDANT",
        }
        resp = client.post("/api/audit", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_urgency"] == "CRITICAL_STAT_PANIC"


class TestChatEndpoint:
    def test_chat_valid_query(self):
        resp = client.post("/api/chat", json={"query": "system status"})
        assert resp.status_code == 200
        assert "response" in resp.json()

    def test_chat_rejects_empty_query(self):
        resp = client.post("/api/chat", json={"query": ""})
        assert resp.status_code == 422

    def test_chat_rejects_phi_query(self):
        resp = client.post("/api/chat", json={"query": "Patient MRN-12345678 status"})
        assert resp.status_code == 400


class TestAuditLogsEndpoint:
    def test_audit_logs_returns_trail(self):
        resp = client.get("/api/audit/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "audit_trail" in data
        assert "verified" in data
        assert data["verified"] is True
