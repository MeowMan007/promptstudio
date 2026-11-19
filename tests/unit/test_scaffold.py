from pathlib import Path


def test_master_plan_lists_first_task() -> None:
    plan = Path(__file__).resolve().parents[2] / "MASTER_PLAN.yaml"
    assert "id: TSK-001" in plan.read_text(encoding="utf-8")
