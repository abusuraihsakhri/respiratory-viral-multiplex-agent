"""
Command Line Interface for Respiratory Viral Multiplex Agent.
"""
import argparse
import csv
import json
import sys
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger, SecurityException

supervisor = SystemSupervisor(model_provider="mock")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="respiratory-viral-multiplex-agent", description="Respiratory Viral Multiplex Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001", help="Unique task / case identifier")
    p_audit.add_argument("--target", default="KEY-TARGET-01", help="Target: specimen, patient key, or genomic target")
    p_audit.add_argument("--primary", type=float, default=28.5, help="Primary metric measurement")
    p_audit.add_argument("--secondary", type=float, default=14.2, help="Secondary metric / kinetic index")
    p_audit.add_argument("--critical", action="store_true", help="Trigger emergency escalation / STAT flag")
    p_audit.add_argument("--status", default="DISCORDANT", help="Status or phenotype descriptor")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  RESPIRATORY VIRAL MULTIPLEX AGENT")
        print(f"  Domain: Antimicrobial Stewardship & Microbiology | Standard: CLSI M100 / EUCAST / CDC NHSN Guidelines")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Respiratory Viral Multiplex Agent Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        from pathlib import Path
        input_path = Path(args.input).resolve()
        output_path = Path(args.output).resolve()
        # Security: prevent path traversal outside working directory
        cwd = Path.cwd().resolve()
        if not input_path.is_relative_to(cwd):
            print(f"Error: Input path must be within the project directory: {input_path}", file=sys.stderr)
            return 1

        if not output_path.is_relative_to(cwd):
            print("Error: Output path must be within the project directory", file=sys.stderr)
            return 1

        try:
            with open(input_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
                if not fieldnames or not {"primary_metric", "metric_primary"}.intersection(fieldnames):
                    raise ValueError("CSV must include primary_metric or metric_primary")
        except (OSError, ValueError, csv.Error, UnicodeDecodeError) as e:
            print(f"Error reading CSV: {e}", file=sys.stderr)
            return 1

        out_fields = fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        out_rows = []
        for r in rows:
            try:
                flag_text = str(r.get("is_critical_flag", r.get("is_stat", r.get("critical_flag", "")))).strip().lower()
                if flag_text not in ("", "0", "1", "true", "false", "yes", "no"):
                    raise ValueError("Invalid is_critical_flag; expected true/false")
                payload = SystemTaskPayload(
                    task_id=r.get("task_id", r.get("case_id", "TASK-01")),
                    target_identifier=r.get("target_identifier", r.get("patient_synthetic_id", "TARGET-01")),
                    primary_metric=float(r.get("primary_metric", r.get("metric_primary", 15.0))),
                    secondary_metric=float(r.get("secondary_metric", r.get("metric_secondary", 5.0))),
                    status_descriptor=r.get("status_descriptor", r.get("status_flag", "NOMINAL")),
                    is_critical_flag=flag_text in ("true", "1", "yes"),
                )
                dossier = supervisor.process_task(payload)
            except (ValueError, TypeError, SecurityException) as e:
                print(f"Skipping malformed or disallowed row: {e}", file=sys.stderr)
                continue
            row_dict = dict(r)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        with open(output_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows({key: _safe_csv_cell(value) for key, value in row.items()} for row in out_rows)
        print(f"Processed {len(out_rows)} records -> {output_path}")
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Respiratory Viral Multiplex Agent API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
