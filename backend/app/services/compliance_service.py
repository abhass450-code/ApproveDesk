from typing import Any


SUPPORTED_OPERATORS = {
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "contains",
    "in",
}


def evaluate_condition(
    actual: Any,
    operator: str,
    expected: Any,
) -> tuple[str, float | None, str]:
    """
    Returns:
        status, gap_value, explanation
    """

    operator = operator.lower().strip()

    if operator not in SUPPORTED_OPERATORS:
        return (
            "NEEDS_REVIEW",
            None,
            f"Unsupported compliance operator: {operator}",
        )

    if actual is None:
        return (
            "NEEDS_REVIEW",
            None,
            "Required value is missing and must be reviewed.",
        )

    try:
        if operator == "eq":
            passed = actual == expected

        elif operator == "neq":
            passed = actual != expected

        elif operator == "gt":
            passed = actual > expected

        elif operator == "gte":
            passed = actual >= expected

        elif operator == "lt":
            passed = actual < expected

        elif operator == "lte":
            passed = actual <= expected

        elif operator == "contains":
            passed = expected in actual

        elif operator == "in":
            passed = actual in expected

        else:
            return (
                "NEEDS_REVIEW",
                None,
                "Rule could not be evaluated automatically.",
            )

    except (TypeError, ValueError):
        return (
            "NEEDS_REVIEW",
            None,
            f"Value '{actual}' could not be compared with '{expected}'.",
        )

    if passed:
        return (
            "PASS",
            0,
            f"Requirement satisfied: {actual} {operator} {expected}.",
        )

    gap = None

    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        gap = expected - actual

    return (
        "FAIL",
        gap,
        f"Requirement not satisfied: {actual} {operator} {expected}.",
    )


def evaluate_rule(rule: Any, values: dict[str, Any]) -> dict[str, Any]:
    actual = values.get(rule.field_key)

    status, gap, explanation = evaluate_condition(
        actual=actual,
        operator=rule.operator,
        expected=rule.expected_value,
    )

    return {
        "rule_id": rule.id,
        "rule_code": rule.code,
        "rule_name": rule.name,
        "rule_version": rule.version,
        "field_key": rule.field_key,
        "operator": rule.operator,
        "expected_value": rule.expected_value,
        "actual_value": actual,
        "status": status,
        "severity": rule.severity,
        "gap_value": gap,
        "explanation": explanation,
        "source_title": rule.source_title,
        "source_url": rule.source_url,
        "source_clause": rule.source_clause,
        "source_verified": rule.source_verified,
        "evidence_document_ids": [],
    }
