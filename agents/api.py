"""
FastAPI REST API Server for Respiratory Viral Multiplex Agent.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Respiratory Viral Multiplex Agent API",
    description="Enterprise Distributed Component Platform (Antimicrobial Stewardship & Microbiology)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Supervisory chat query")

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Query must not be empty or whitespace-only")
        return v.strip()


class AuditPayload(BaseModel):
    """Validated audit payload with strict string length limits."""
    task_id: str = Field(..., min_length=1, max_length=128)
    target_identifier: str = Field(..., min_length=1, max_length=128)
    primary_metric: float = Field(..., ge=-1e6, le=1e6, allow_inf_nan=False)
    secondary_metric: float = Field(default=0.0, ge=-1e6, le=1e6, allow_inf_nan=False)
    status_descriptor: str = Field(default="NOMINAL", max_length=64)
    is_critical_flag: bool = False

    @field_validator("task_id", "target_identifier", "status_descriptor")
    @classmethod
    def check_no_phi(cls, v, info):
        try:
            PHIGuard.assert_no_phi(v)
        except SecurityException:
            raise ValueError(f"PHI violation in field '{info.field_name}': sensitive data not allowed")
        return v


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "respiratory-viral-multiplex-agent", "domain": "Antimicrobial Stewardship & Microbiology", "standard": "Project-defined demonstration thresholds (not clinical guidance)", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    """Prometheus-compatible text-format metrics endpoint."""
    trail_len = len(AuditLogger.get_trail())
    dossier_count = len(supervisor.dossier_registry)
    lines = [
        "# HELP dossiers_processed_total Total dossiers processed by the supervisor",
        "# TYPE dossiers_processed_total counter",
        f'dossiers_processed_total{{system="respiratory-viral-multiplex-agent"}} {dossier_count}',
        "",
        "# HELP audit_blocks_total Total HMAC-SHA256 audit blocks signed",
        "# TYPE audit_blocks_total counter",
        f'audit_blocks_total{{system="respiratory-viral-multiplex-agent"}} {trail_len}',
        "",
        "# HELP system_status Current system operational status (1=healthy)",
        "# TYPE system_status gauge",
        'system_status{system="respiratory-viral-multiplex-agent"} 1',
    ]
    return Response(content="\n".join(lines) + "\n", media_type="text/plain")


@app.post("/api/audit")
def api_audit(payload: AuditPayload):
    task_payload = SystemTaskPayload(
        task_id=payload.task_id,
        target_identifier=payload.target_identifier,
        primary_metric=payload.primary_metric,
        secondary_metric=payload.secondary_metric,
        status_descriptor=payload.status_descriptor,
        is_critical_flag=payload.is_critical_flag,
    )
    dossier = supervisor.process_task(task_payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=400, detail="Query contains a disallowed identifier")


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
