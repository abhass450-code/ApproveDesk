from types import SimpleNamespace

from app.services.compliance_service import (
    evaluate_condition,
    evaluate_rule,
)


def test_greater_than_passes():
    status, gap, explanation = evaluate_condition(60, "gte", 50)

    assert status == "PASS"
    assert gap == 0
    assert "Requirement satisfied" in explanation


def test_greater_than_fails():
    status, gap, explanation = evaluate_condition(40, "gte", 50)

    assert status == "FAIL"
    assert gap == 10
    assert "Requirement not satisfied" in explanation


def test_missing_value_needs_review():
    status, gap, explanation = evaluate_condition(None, "gte", 50)

    assert status == "NEEDS_REVIEW"
    assert gap is None
    assert "missing" in explanation.lower()


def test_invalid_comparison_needs_review():
    status, gap, explanation = evaluate_condition(
        "abc",
        "gte",
        50,
    )

    assert status == "NEEDS_REVIEW"
    assert gap is None


def test_equal_condition():
    status, gap, _ = evaluate_condition(50, "eq", 50)

    assert status == "PASS"
    assert gap == 0


def test_not_equal_condition():
    status, gap, _ = evaluate_condition(40, "neq", 50)

    assert status == "PASS"
    assert gap == 0


def test_contains_condition():
    status, gap, _ = evaluate_condition(
        ["CSE", "ECE"],
        "contains",
        "CSE",
    )

    assert status == "PASS"
    assert gap == 0


def test_rule_evaluation():
    rule = SimpleNamespace(
        id=1,
        code="FACULTY_MIN",
        name="Minimum Faculty",
        version=1,
        field_key="faculty_count",
        operator="gte",
        expected_value=10,
        severity="HIGH",
        source_title="AICTE Norms",
        source_url=None,
        source_clause="Faculty Requirements",
        source_verified=True,
    )

    result = evaluate_rule(
        rule,
        {"faculty_count": 7},
    )

    assert result["status"] == "FAIL"
    assert result["actual_value"] == 7
    assert result["expected_value"] == 10
    assert result["gap_value"] == 3
