"""
Automated Pytest for CLI batch processing validation and security.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import csv
import os
import tempfile
import pytest
from cli import main


@pytest.fixture
def project_tmp_dir():
    """Create a temporary directory inside the project for batch tests."""
    project_dir = Path(__file__).parent.parent.resolve()
    tmp_dir = project_dir / "_test_tmp"
    tmp_dir.mkdir(exist_ok=True)
    yield tmp_dir
    # Cleanup
    import shutil
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)


class TestCLIBatchValidation:
    def test_batch_creates_output_file(self, project_tmp_dir):
        """Batch processing should create a valid output CSV."""
        input_csv = project_tmp_dir / "input.csv"
        output_csv = project_tmp_dir / "output.csv"

        with open(input_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["task_id", "target_identifier", "primary_metric", "secondary_metric", "status_descriptor", "is_critical_flag"])
            writer.writerow(["T1", "KEY-01", "10.0", "5.0", "NOMINAL", "False"])

        result = main(["batch", "-i", str(input_csv), "-o", str(output_csv)])
        assert result == 0
        assert output_csv.exists()

    def test_batch_output_has_expected_columns(self, project_tmp_dir):
        """Output should contain original columns plus computed ones."""
        input_csv = project_tmp_dir / "input.csv"
        output_csv = project_tmp_dir / "output.csv"

        with open(input_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["task_id", "target_identifier", "primary_metric", "secondary_metric", "status_descriptor", "is_critical_flag"])
            writer.writerow(["T1", "KEY-01", "10.0", "5.0", "NOMINAL", "False"])

        main(["batch", "-i", str(input_csv), "-o", str(output_csv)])

        with open(output_csv, "r") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert "overall_urgency" in row
            assert "integrity_status" in row
            assert "total_alerts" in row
            assert "audit_hash" in row

    def test_batch_handles_malformed_rows_gracefully(self, project_tmp_dir):
        """Malformed rows should be skipped, not crash the batch."""
        input_csv = project_tmp_dir / "input.csv"
        output_csv = project_tmp_dir / "output.csv"

        with open(input_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["task_id", "target_identifier", "primary_metric", "secondary_metric", "status_descriptor", "is_critical_flag"])
            writer.writerow(["T1", "KEY-01", "10.0", "5.0", "NOMINAL", "False"])
            writer.writerow(["T2", "KEY-02", "INVALID", "5.0", "NOMINAL", "False"])
            writer.writerow(["T3", "KEY-03", "15.0", "8.0", "NOMINAL", "False"])

        result = main(["batch", "-i", str(input_csv), "-o", str(output_csv)])
        assert result == 0

        with open(output_csv, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2  # malformed row skipped

    def test_batch_rejects_path_traversal(self):
        """Batch processing should reject input paths outside the project directory."""
        # Create a file outside the project directory
        outside_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        try:
            outside_file.write("task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag\n")
            outside_file.write("T1,KEY-01,10.0,5.0,NOMINAL,False\n")
            outside_file.close()

            result = main(["batch", "-i", outside_file.name, "-o", "output.csv"])
            assert result == 1  # Should return error code
        finally:
            os.unlink(outside_file.name)
