# Respiratory Viral Multiplex Agent

> **Domain:** Infectious Disease Surveillance & Microbiology
> **Reference Guidelines & Standards:** CLSI M100, EUCAST & CDC NHSN Clinical Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

**Respiratory Viral Multiplex Agent** is an analytical and computational platform implementing Syndromic Multiplex PCR evaluation and Hospital Cohorting Rules Engine. It processes clinical metrics through specialized worker agents and produces consensus dossiers with tamper-evident audit trails.

---

## Key Capabilities

### Core Algorithmic & Evaluation Engines

- **Severity Evaluation** — dedicated module for severity evaluation and state verification.
- **DomainKnowledgeRegistry** — enterprise domain rules, guideline matrices, and evidence benchmarks.
- **AgentAlert** — dedicated module for agent alert evaluation and state verification.
- **TargetDeconvolutionAgent** — primary metric & baseline quality auditor.
- **IsolationProtocolDispatcherAgent** — STAT kinetics & closed-loop escalation auditor.
- **AntiviralWindowEvaluatorAgent** — biomarker & concordance triager.

### Security Features

- **Zero-PHI Outbound Interceptor** — AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
- **Tamper-Evident HMAC-SHA256 Audit Trail** — chained, cryptographically signed logs for every evaluation.
- **Input Validation** — strict payload validation with bounds checking and PHI detection.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/respiratory-viral-multiplex-agent.git
cd respiratory-viral-multiplex-agent

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Optional: Set audit secret key (recommended for production)
export AUDIT_SECRET_KEY="your-secure-random-key-here"
```

---

## CLI Usage

### 1. Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target SPECIMEN-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Interactive Chat
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### CLI Parameters

| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--task-id` | Unique task / case identifier | `TASK-2026-001` |
| `--target` | Target: specimen, patient key, or genomic target | `KEY-TARGET-01` |
| `--primary` | Primary metric measurement | `28.5` |
| `--secondary` | Secondary metric / kinetic index | `14.2` |
| `--critical` | Trigger emergency escalation / STAT flag | `False` |
| `--status` | Status or phenotype descriptor | `DISCORDANT` |

---

## REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus-compatible metrics |
| `POST` | `/api/audit` | Submit task for evaluation |
| `POST` | `/api/chat` | Query supervisory chat |
| `GET` | `/api/audit/logs` | Retrieve audit trail |

---

## Testing

```bash
# Run all tests
pytest -v

# Run specific test files
pytest tests/ -v
pytest test_resp_viral_sentinel.py -v
```

---

## Container Deployment

```bash
# Build and run with Docker
docker build -t respiratory-viral-multiplex-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key respiratory-viral-multiplex-agent

# Or use docker-compose
AUDIT_SECRET_KEY=your-secret-key docker-compose up
```

---

## Project Structure

```
respiratory-viral-multiplex-agent/
├── agents/                          # Core agent modules
│   ├── api.py                       # FastAPI REST server
│   ├── base.py                      # Security, PHI guard, audit trail
│   ├── models.py                    # Pydantic data models
│   ├── supervisor.py                # Master orchestrator
│   ├── workers.py                   # Specialized evaluation workers
│   ├── llm_factory.py               # LLM provider factory
│   ├── learning.py                  # Bayesian calibration engine
│   ├── metrics.py                   # Prometheus metrics collector
│   └── streamer.py                  # WebSocket telemetry
├── respiratory_viral_multiplex_agent/
│   ├── agents.py                    # Domain-specific sub-agents
│   ├── engine.py                    # Clinical algorithmic engine
│   ├── models.py                    # Clinical data models
│   ├── server.py                    # FastAPI app factory
│   └── cli.py                       # Alternative CLI entry point
├── tests/                           # Test suite
├── web/                             # Operations console (HTML)
├── cli.py                           # Main CLI entry point
├── enrichment.py                    # Enrichment feature engines
├── simulator.py                     # High-throughput simulation
├── sample.csv                       # Sample batch input
├── sample_payload.json              # Sample API payload
├── Dockerfile                       # Container build
├── docker-compose.yml               # Container orchestration
└── pyproject.toml                   # Project metadata
```

---

## Security Notes

- **Audit Secret Key**: Set the `AUDIT_SECRET_KEY` environment variable in production. Without it, an ephemeral key is generated at runtime (audit trail will not persist across restarts).
- **PHI Guard**: All outbound data is inspected for PHI patterns. Payloads containing SSNs, MRNs, or patient identifiers are rejected.
- **Input Validation**: API endpoints enforce strict bounds on numeric fields and string lengths.
- **Path Traversal Protection**: Batch processing validates that input paths remain within the project directory.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
