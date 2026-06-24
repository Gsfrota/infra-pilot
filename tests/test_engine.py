from infrapilot.engines import get_engine
from infrapilot.engines.native import NativeEngine


def test_get_engine_resolves_native():
    assert get_engine("native") is NativeEngine


def test_get_engine_rejects_unknown():
    try:
        get_engine("does-not-exist")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_full_pipeline_remediates_and_improves_score():
    result = NativeEngine(simulate=True).run(auto_remediate=True)

    stage_names = [s.name for s in result.stages]
    assert stage_names == ["provision", "configure", "observe", "audit", "remediate"]

    # the seeded desired state has violations, and auto-remediation must fix them
    assert result.applied_count >= 1
    remediate = next(s for s in result.stages if s.name == "remediate")
    assert remediate.details["score_after"] >= remediate.details["score_before"]
    # after remediation the loop should reach (near) full compliance
    assert result.compliance.score >= remediate.details["score_before"]


def test_dry_run_proposes_without_applying():
    result = NativeEngine(simulate=True).run(auto_remediate=False)
    assert result.applied_count == 0
    assert any(r.applied is False for r in result.remediations)
