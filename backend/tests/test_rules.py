"""
Phase 1 rule-engine tests (Member 3).

Covers:
- Every bad fixture triggers exactly its expected rule.
- Every good fixture produces zero findings.
- All five starter rules load.
- Parser security edge cases: oversized file, deep nesting, YAML alias abuse,
  missing file, and the wildcard-value regression (the Member 2 bug).
"""

import json
from pathlib import Path

import pytest

from parser import SecureParser
from rule_engine import RuleEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = REPO_ROOT / "rules"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

engine = RuleEngine(rules_directory=str(RULES_DIR))
parser = SecureParser()

# Each bad fixture must trigger exactly this set of rule IDs.
BAD_EXPECTATIONS = {
    "s3_public_read.json": {"CIS-AWS-001"},
    "security_group_open.yaml": {"CIS-AWS-002"},
    "iam_wildcard_action.json": {"CIS-AWS-003"},
    "s3_encryption.json": {"CIS-AWS-004"},
    "iam_wildcard_principal.yaml": {"CIS-AWS-005"},
}


def _findings_for(path):
    return engine.evaluate(parser.parse(str(path)))


# ---------------- Rule fixtures ---------------- #

@pytest.mark.parametrize("filename,expected", BAD_EXPECTATIONS.items())
def test_bad_fixture_triggers_expected_rule(filename, expected):
    rule_ids = {f["rule_id"] for f in _findings_for(FIXTURES / "bad" / filename)}
    assert rule_ids == expected


@pytest.mark.parametrize("path", sorted((FIXTURES / "good").glob("*")))
def test_good_fixture_has_no_findings(path):
    assert _findings_for(path) == []


def test_all_five_rules_loaded():
    ids = {r["rule_id"] for r in engine.rules}
    assert {
        "CIS-AWS-001", "CIS-AWS-002", "CIS-AWS-003", "CIS-AWS-004", "CIS-AWS-005",
    } <= ids


# ---------------- Parser security edge cases ---------------- #

def test_oversized_file_rejected(tmp_path):
    f = tmp_path / "big.json"
    f.write_text("0" * (2 * 1024 * 1024 + 10))
    with pytest.raises(ValueError):
        parser.parse(str(f))


def test_deep_nesting_rejected(tmp_path):
    payload = "0"
    for _ in range(50):  # well past MAX_DEPTH (20)
        payload = "[" + payload + "]"
    f = tmp_path / "deep.json"
    f.write_text(payload)
    with pytest.raises(ValueError):
        parser.parse(str(f))


def test_yaml_alias_abuse_rejected(tmp_path):
    f = tmp_path / "bomb.yaml"
    f.write_text("a: &anchor [1, 2, 3]\nb: *anchor\n")
    with pytest.raises(ValueError):
        parser.parse(str(f))


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        parser.parse(str(tmp_path / "does_not_exist.json"))


def test_wildcard_value_regression(tmp_path):
    """A wildcard value (e.g. "s3:*") must PARSE and be detectable.

    This is the regression guard for the original Member 2 parser bug, which
    rejected any input containing '*' before parsing.
    """
    f = tmp_path / "iam.json"
    f.write_text(json.dumps(
        {"resource_id": "p", "resource_type": "iam_policy", "action": "s3:*"}
    ))
    data = parser.parse(str(f))
    assert {x["rule_id"] for x in engine.evaluate(data)} == {"CIS-AWS-003"}
