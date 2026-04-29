"""Tests for the CocoIndex-backed signal ingestion/enrichment pipeline."""

from pathlib import Path

from cortex_core.config import CortexConfig
from cortex_core.engine import CortexEngine


def _make_engine(tmp_data_dir: Path) -> CortexEngine:
    return CortexEngine(CortexConfig(data_dir=tmp_data_dir))


def test_new_signal_ingestion_persists_raw_and_enriched(tmp_data_dir):
    engine = _make_engine(tmp_data_dir)
    payload = engine.capture_signal(
        text="Decision: ship offline queue retry with exponential backoff.",
        source="capture",
        source_id="release-offline-1",
        project="SimpliXio",
        tags=["offline", "release"],
    )

    assert payload is not None
    cocoindex = payload.get("cocoindex", {})
    assert cocoindex.get("raw", {}).get("status") == "created"
    assert cocoindex.get("enriched", {}).get("status") == "created"

    stats = engine.signal_matcher.cocoindex_stats()
    assert stats["raw_signals"] == 1
    assert stats["enriched_signals"] == 1


def test_changed_signal_reprocesses_incrementally(tmp_data_dir):
    engine = _make_engine(tmp_data_dir)
    first = engine.capture_signal(
        text="Decision: keep current launch checklist.",
        source="capture",
        source_id="launch-checklist",
        project="SimpliXio",
    )
    second = engine.capture_signal(
        text="Decision: update launch checklist with TestFlight feedback.",
        source="capture",
        source_id="launch-checklist",
        project="SimpliXio",
    )

    assert first is not None and second is not None
    assert second["cocoindex"]["raw"]["status"] == "updated"
    assert second["cocoindex"]["enriched"]["status"] in {"updated", "created"}
    assert second["signal"]["id"] == first["signal"]["id"]
    assert second["signal"]["text"].startswith("Decision: update launch checklist")


def test_unchanged_signal_skips_recompute(tmp_data_dir):
    engine = _make_engine(tmp_data_dir)
    first = engine.capture_signal(
        text="Question: should we keep weekly review deterministic?",
        source="capture",
        source_id="weekly-review-question",
        project="SimpliXio",
    )
    second = engine.capture_signal(
        text="Question: should we keep weekly review deterministic?",
        source="capture",
        source_id="weekly-review-question",
        project="SimpliXio",
    )

    assert first is not None and second is not None
    assert second["cocoindex"]["raw"]["status"] == "unchanged"
    assert second["cocoindex"]["enriched"]["recomputed"] is False
    assert second["signal"]["id"] == first["signal"]["id"]


def test_sensitivity_classification_persists_in_enriched_store(tmp_data_dir):
    engine = _make_engine(tmp_data_dir)
    payload = engine.capture_signal(
        text="Internal client roadmap decision with confidential pricing detail.",
        source="capture",
        source_id="client-roadmap-1",
        project="SimpliXio",
        tags=["internal"],
    )

    assert payload is not None
    assert payload["signal"]["sensitivity"] in {"private", "sensitive", "internal"}
    trace = payload["signal"].get("trace_metadata", {})
    assert trace.get("pipeline") == "cocoindex_signals"
    assert trace.get("raw_signal_id") == "capture:client-roadmap-1"


def test_pipeline_fallback_without_cocoindex_package(tmp_data_dir):
    engine = _make_engine(tmp_data_dir)
    stats = engine.signal_matcher.cocoindex_stats()
    assert stats["backend"] in {"cocoindex", "fallback"}

    payload = engine.capture_signal(
        text="Reflection: simplify queue defaults for calm UX.",
        source="capture",
        source_id="fallback-check-1",
    )
    assert payload is not None
    assert "cocoindex" in payload


def test_pipeline_failure_falls_back_to_internal_normalisation(tmp_data_dir, monkeypatch):
    engine = _make_engine(tmp_data_dir)

    def _fail_upsert(_: dict):
        raise RuntimeError("forced pipeline failure")

    monkeypatch.setattr(engine.signal_matcher.cocoindex_pipeline, "upsert_raw_signal", _fail_upsert)
    payload = engine.capture_signal(
        text="Thought: keep fallback robust during ingestion failures.",
        source="capture",
        source_id="forced-failure-1",
    )

    assert payload is not None
    assert payload["cocoindex"]["status"] == "fallback"
    assert payload["signal"]["trace_metadata"]["status"] == "fallback"


def test_existing_ranking_layer_still_works_with_cocoindex_pipeline(tmp_data_dir):
    engine = _make_engine(tmp_data_dir)
    for idx in range(6):
        engine.capture_signal(
            text=f"Tension {idx}: offline sync retries still unclear.",
            source="capture",
            source_id=f"signal-{idx}",
            project="SimpliXio",
            tags=["offline", "sync"],
        )

    ranked = engine.build_signal_matching_output()
    assert len(ranked["top_priorities"]) <= 3
    assert len(ranked["decision_queue"]) <= 5
    assert len(ranked["action_ready_queue"]) <= 5
