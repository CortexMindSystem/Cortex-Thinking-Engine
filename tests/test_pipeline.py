"""Unit tests for the pipeline orchestrator."""

from cortex_core.pipeline import Pipeline, StepResult, StepStatus


class TestStepResult:
    def test_defaults(self):
        sr = StepResult(name="test")
        assert sr.status == StepStatus.PENDING
        assert sr.error is None

    def test_to_dict(self):
        sr = StepResult(name="test", status=StepStatus.SUCCESS)
        d = sr.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "success"


class TestPipeline:
    def test_single_step_success(self):
        pipe = Pipeline("Test")
        pipe.add_step("step1", lambda: "done")
        result = pipe.run()
        assert result.success
        assert len(result.steps) == 1
        assert result.steps[0].status == StepStatus.SUCCESS
        assert result.steps[0].output == "done"

    def test_multiple_steps(self):
        pipe = Pipeline("Test")
        pipe.add_step("a", lambda: 1)
        pipe.add_step("b", lambda: 2)
        pipe.add_step("c", lambda: 3)
        result = pipe.run()
        assert result.success
        assert len(result.steps) == 3

    def test_step_failure_stops_pipeline(self):
        pipe = Pipeline("Test")
        pipe.add_step("ok", lambda: "fine")
        pipe.add_step("fail", lambda: (_ for _ in ()).throw(ValueError("boom")))
        pipe.add_step("skip", lambda: "never")
        result = pipe.run(stop_on_failure=True)
        assert not result.success
        assert result.steps[0].status == StepStatus.SUCCESS
        assert result.steps[1].status == StepStatus.FAILED
        assert "ValueError" in result.steps[1].error

    def test_duration_tracked(self):
        pipe = Pipeline("Test")
        pipe.add_step("step", lambda: None)
        result = pipe.run()
        assert result.duration_s >= 0
        assert result.steps[0].duration_s >= 0

    def test_to_dict(self):
        pipe = Pipeline("Test")
        pipe.add_step("step", lambda: None)
        result = pipe.run()
        d = result.to_dict()
        assert d["name"] == "Test"
        assert d["success"] is True
        assert "steps" in d

    def test_decorator_registration(self):
        pipe = Pipeline("Test")

        @pipe.step("decorated")
        def my_step():
            return 42

        result = pipe.run()
        assert result.success
        assert result.steps[0].output == 42

    def test_callbacks(self):
        started = []
        ended = []

        pipe = Pipeline("Test")
        pipe.on_step_start(lambda name: started.append(name))
        pipe.on_step_end(lambda sr: ended.append(sr.name))
        pipe.add_step("step1", lambda: None)
        pipe.add_step("step2", lambda: None)
        pipe.run()

        assert started == ["step1", "step2"]
        assert ended == ["step1", "step2"]
