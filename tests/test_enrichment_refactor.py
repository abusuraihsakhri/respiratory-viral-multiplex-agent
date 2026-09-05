"""
Tests verifying the refactored enrichment module maintains backward compatibility
and that the base class extraction works correctly.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from enrichment import (
    BaseEnrichmentEngine,
    EnrichmentResult,
    FeaturesEngine,
    AntimicrobialStewardshipDashboardEngine,
    BloodCultureEarlyAlertEngine,
    OutbreakDetectionAlgorithmEngine,
    MdroSurveillanceEngine,
    AntibiogramGeneratorEngine,
    AntifungalStewardshipEngine,
    VaccinationStatusTracker,
    RespiratoryviralmultiplexagentEnrichmentSuite,
    enrichment_suite,
    # Backward-compatible aliases
    FeaturesEngineResult,
    VaccinationStatusTrackerResult,
)


class TestBaseEnrichmentEngine:
    def test_default_feature_name(self):
        engine = BaseEnrichmentEngine()
        assert engine.FEATURE_NAME == "Enrichment"

    def test_custom_threshold(self):
        engine = BaseEnrichmentEngine(threshold=5.0)
        assert engine.threshold == 5.0

    def test_config_storage(self):
        engine = BaseEnrichmentEngine(config={"key": "value"})
        assert engine.config == {"key": "value"}

    def test_default_config_is_dict(self):
        engine = BaseEnrichmentEngine()
        assert engine.config == {}

    def test_history_starts_empty(self):
        engine = BaseEnrichmentEngine()
        assert len(engine.history) == 0

    def test_optimal_status_below_threshold(self):
        engine = BaseEnrichmentEngine(threshold=10.0)
        result = engine.evaluate(primary_value=5.0)
        assert result.status == "OPTIMAL"

    def test_warning_status_above_threshold(self):
        engine = BaseEnrichmentEngine(threshold=10.0)
        result = engine.evaluate(primary_value=15.0)
        assert result.status == "WARNING"

    def test_critical_status_above_double_threshold(self):
        engine = BaseEnrichmentEngine(threshold=10.0)
        result = engine.evaluate(primary_value=25.0)
        assert result.status == "CRITICAL_ALERT"

    def test_score_is_rounded(self):
        engine = BaseEnrichmentEngine()
        result = engine.evaluate(primary_value=1.23456)
        assert result.score == 1.235

    def test_metrics_include_secondary(self):
        engine = BaseEnrichmentEngine()
        result = engine.evaluate(primary_value=5.0, secondary_value=2.5)
        assert result.metrics["secondary"] == 2.5

    def test_recommendations_populated(self):
        engine = BaseEnrichmentEngine(threshold=10.0)
        optimal = engine.evaluate(5.0)
        assert len(optimal.recommendations) > 0

    def test_alerts_populated_for_critical(self):
        engine = BaseEnrichmentEngine(threshold=10.0)
        result = engine.evaluate(25.0)
        assert len(result.alerts) > 0

    def test_history_appended(self):
        engine = BaseEnrichmentEngine()
        engine.evaluate(1.0)
        engine.evaluate(2.0)
        assert len(engine.history) == 2


class TestConcreteEngines:
    def test_features_engine_name(self):
        engine = FeaturesEngine()
        assert engine.FEATURE_NAME == "Features"

    def test_antimicrobial_engine_name(self):
        engine = AntimicrobialStewardshipDashboardEngine()
        assert engine.FEATURE_NAME == "Antimicrobial Stewardship Dashboard"

    def test_vaccination_engine_name(self):
        engine = VaccinationStatusTracker()
        assert engine.FEATURE_NAME == "Vaccination Status Tracker"

    def test_all_engines_inherit_base(self):
        engines = [
            FeaturesEngine(),
            AntimicrobialStewardshipDashboardEngine(),
            BloodCultureEarlyAlertEngine(),
            OutbreakDetectionAlgorithmEngine(),
            MdroSurveillanceEngine(),
            AntibiogramGeneratorEngine(),
            AntifungalStewardshipEngine(),
            VaccinationStatusTracker(),
        ]
        for engine in engines:
            assert isinstance(engine, BaseEnrichmentEngine)


class TestBackwardCompatibility:
    def test_result_alias_exists(self):
        assert FeaturesEngineResult is EnrichmentResult
        assert VaccinationStatusTrackerResult is EnrichmentResult

    def test_global_suite_works(self):
        results = enrichment_suite.execute_all(primary_val=0.5, secondary_val=0.2)
        assert len(results) == 8

    def test_suite_get_history(self):
        suite = RespiratoryviralmultiplexagentEnrichmentSuite()
        suite.execute_all(primary_val=1.0)
        history = suite.get_history()
        assert len(history) == 8
        for engine_name, entries in history.items():
            assert len(entries) == 1
