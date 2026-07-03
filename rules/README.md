# AWS Cloud Security Rules

This directory contains the YAML-based, declarative security rules used by the
CSPM rule engine (`backend/src/rule_engine.py`). Rules are **data, not code** —
new checks are added by dropping a new YAML file here, with no engine changes.

## Rule Structure

Each rule follows the schema documented in `spec.yaml` (which the engine skips).

### Top-level fields

| Field        | Description                                       |
| ------------ | ------------------------------------------------- |
| rule_id      | Unique identifier for the rule                    |
| name         | Human-readable rule name                          |
| severity     | Risk level (Low, Medium, High, Critical)          |
| compliance   | Mapped control IDs (`cis_aws`, `nist_csf`)        |
| condition    | The condition evaluated against each resource     |
| remediation  | Recommended fix for the issue                     |

### Condition fields

| Field         | Description                                              |
| ------------- | ------------------------------------------------------- |
| resource_type | Resource type the rule applies to (e.g. `s3_bucket`)    |
| eval_path     | Dot-path to the field being checked (e.g. `ingress.cidr`)|
| equals        | Exact value match                                       |
| contains      | Substring / membership match                            |
| regex         | Regular-expression match                                |
| gte           | Numeric greater-than-or-equal                           |
| lte           | Numeric less-than-or-equal                              |

Use **exactly one** operator per rule.

## Implemented Rules

| Rule ID     | Name                          | Severity | resource_type    | CIS / NIST        |
| ----------- | ----------------------------- | -------- | ---------------- | ----------------- |
| CIS-AWS-001 | S3 Bucket Public Read Access  | High     | s3_bucket        | 2.1.5 / PR.AC-3   |
| CIS-AWS-002 | Security Group Open Ingress   | High     | security_group   | 5.2 / PR.AC-5     |
| CIS-AWS-003 | IAM Policy Wildcard Action    | Critical | iam_policy       | 1.16 / PR.AC-4    |
| CIS-AWS-004 | S3 Bucket Encryption Disabled | Medium   | s3_bucket        | 2.1.1 / PR.DS-1   |
| CIS-AWS-005 | IAM Policy Wildcard Principal | Critical | iam_policy       | 1.16 / PR.AC-4    |

## Notes

- Only CIS **control IDs** are referenced — no CIS benchmark text is
  redistributed (licensing). NIST CSF subcategory IDs are public domain.
- The CIS control numbers above should be re-verified against the exact CIS AWS
  Foundations Benchmark version the team standardises on.
- Every rule must have a paired **good** fixture (does not trigger) and **bad**
  fixture (triggers) under `backend/tests/fixtures/` — Member 3's deliverable.
