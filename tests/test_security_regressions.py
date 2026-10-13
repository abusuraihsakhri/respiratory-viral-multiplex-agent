"""Regression tests for signed audit records, input rejection and CLI batch behavior."""
import csv
from pathlib import Path

import pytest
from pydantic import ValidationError

from agents.base import AuditTrail
from agents.models import SystemTaskPayload
from cli import main


def test_audit_verifies_each_hmac_not_just_chain_links():
    audit = AuditTrail("unit-test-only-key")
    audit.log("tester", "test", "CREATE", {"state": "ok"})
    audit.log("tester", "test", "CHECK", {"state": "ok"})
    assert audit.verify_integrity()
    audit.logs[0]["actor"] = "forged"
    assert not audit.verify_integrity()


def test_audit_snapshot_cannot_mutate_internal_ledger():
    audit = AuditTrail("unit-test-only-key")
    audit.log("tester", "test", "CREATE", {"state": "ok"})
    snapshot = audit.get_trail()
    snapshot[0]["current_hash"] = "forged"
    snapshot.clear()
    assert audit.verify_integrity()
    assert len(audit.get_trail()) == 1


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_model_rejects_nonfinite_metrics(bad):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T1", target_identifier="SYN-1", primary_metric=bad)


def test_batch_skips_bad_priority_flags_and_phi(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = Path("input.csv")
    target = Path("output.csv")
    with source.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["task_id", "target_identifier", "primary_metric", "is_critical_flag"])
        writer.writerow(["SAFE-001", "SYN-1", "10", "false"])
        writer.writerow(["SAFE-002", "SYN-2", "12", "maybe"])
        writer.writerow(["MRN: 12345678", "SYN-3", "12", "false"])
    assert main(["batch", "-i", str(source), "-o", str(target)]) == 0
    with target.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [r["task_id"] for r in rows] == ["SAFE-001"]


def test_batch_rejects_missing_required_columns(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("input.csv").write_text("task_id\nTEST\n", encoding="utf-8")
    assert main(["batch", "-i", "input.csv", "-o", "output.csv"]) == 1
    assert not Path("output.csv").exists()


def test_primary_batch_accepts_bundled_sample_schema(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("sample.csv").write_text(
        "case_id,patient_synthetic_id,metric_primary,metric_secondary,is_stat,status_flag\n"
        "CASE-01,SYN-01,10,4,False,NORMAL\n", encoding="utf-8"
    )
    assert main(["batch", "-i", "sample.csv", "-o", "output.csv"]) == 0
    with Path("output.csv").open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    assert row["overall_urgency"] == "ROUTINE"


def test_alternate_batch_false_flag_does_not_become_true(tmp_path):
    from respiratory_viral_multiplex_agent.cli import main as alternate_main
    source, target = tmp_path / "sample.csv", tmp_path / "result.csv"
    source.write_text(
        "case_id,patient_synthetic_id,metric_primary,metric_secondary,is_stat,status_flag\n"
        "CASE-01,SYN-01,10,4,False,NORMAL\n", encoding="utf-8"
    )
    assert alternate_main(["batch", "-i", str(source), "-o", str(target)]) == 0
    with target.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    assert row["stat_critical_alerts"] == "0"
