# Respiratory Viral Multiplex Agent

A qualitative respiratory-panel result organizer, with separate Python research/demo audit tools.

## Browser application

Open **web/index.html** directly in a modern browser, or serve the repository's static files. GitHub Pages publication is configured by `.github/workflows/pages.yml`.

- Paste or import a **two-column CSV** with the header `target,result` (or `pathogen,status`).
- Accepted results: **Detected**, **Not detected**, **Invalid**, **Indeterminate**, **Not tested**; Positive, Negative, and Inconclusive are recognized aliases.
- Review counts and an explicit incomplete-results indicator.
- Export a normalized CSV or JSON summary.
- Files are processed entirely in the browser. There is no remote API request, login, cookie, or browser data storage. Refreshing clears results.

Example:

```csv
target,result
Influenza A,Detected
Influenza B,Not detected
RSV,Indeterminate
SARS-CoV-2,Not detected
```

**Scope and limitations:** The browser tool reports the statuses supplied by the user; it does not establish the set of targets in a particular commercial assay, validate controls, establish a diagnosis, or recommend isolation, cohorting, or antiviral treatment. A negative result does not exclude infection. Follow the assay manufacturer's instructions and locally approved protocols. Do not enter identifiable patient data.

## Python demonstrations

The repository also contains two historically separate Python implementations:

- `cli.py` and `agents/`: the original Pydantic/FastAPI demonstration with generic primary/secondary metrics, a CLI, CSV batch processing, an in-memory audit ledger, and optional REST endpoints.
- `respiratory_viral_multiplex_agent/`: a separate rule-based example exposing its own CLI and optional app factory.
- `resp_viral_sentinel.py` and `enrichment.py`: earlier standalone prototype/utility modules retained for compatibility.

**Important:** Hard-coded numerical thresholds and categorical outputs in these Python demonstrations are *not* validated respiratory-virus assay cutoffs or independently verified CDC, WHO, CLSI, or EUCAST clinical recommendations. They must not be used to make patient-care decisions.

### Installation

Requires Python 3.9 or newer. The CI matrix verifies Python 3.10–3.12.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[api,test]"
python -m pytest -q
```

### Command line

```bash
python cli.py audit --task-id DEMO-01 --target SYNTH-01 --primary 12 --secondary 5 --status NOMINAL
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

CSV batch processing requires `primary_metric` and permits optional task, target, secondary metric, descriptor, and true/false priority columns. Malformed or disallowed rows are skipped with a warning. Batch input and output must remain within the current working directory.

The alternate installed console script is `respiratory-viral-multiplex-engine`. The FastAPI service provides `GET /health`, `GET /metrics`, `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`.

### Local API and Docker

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The Docker Compose example binds port 8000 to localhost. The API itself has **no authentication** and should not be publicly exposed without an appropriate security layer. HMAC audit entries are kept **in memory**, not on durable storage; a per-process ephemeral key is generated if `AUDIT_SECRET_KEY` is unset. HMAC integrity verifies the local stored metadata, not a persistent or independently witnessed audit log.

The regex-based identifier guard catches a limited set of obvious patterns; it is **not HIPAA de-identification or a guarantee of zero PHI**. Use synthetic, non-identifying data only.

## Development and verification

```bash
python -m pytest -q
python -m compileall -q agents respiratory_viral_multiplex_agent
node --check web/app.js
node --test tests/test_browser.cjs
```

GitHub Actions runs the Python suite on three Python versions and browser parser tests on Node.js. The browser application uses standard HTML/CSS/JavaScript and requires no Python runtime, Pyodide, or server. It is intended for current desktop/mobile browsers supporting `File.text()` and `Blob` downloads.

## License

MIT. See [LICENSE](LICENSE).
