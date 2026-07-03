"""seed compliance_map with the five Phase 1 rules

Revision ID: b2c3d4e5f6a7
Revises: 2f5602bdb143
Create Date: 2026-07-02 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "2f5602bdb143"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# CIS control IDs, NIST CSF subcategory IDs and remediation text copied from the
# five declarative rules in /rules (CIS-AWS-001..005).
_SEED = [
    {
        "rule_id": "CIS-AWS-001",
        "cis_control_id": "2.1.5",
        "nist_id": "PR.AC-3",
        "remediation_steps": (
            "Disable public read access and enable S3 Block Public Access on the bucket."
        ),
    },
    {
        "rule_id": "CIS-AWS-002",
        "cis_control_id": "5.2",
        "nist_id": "PR.AC-5",
        "remediation_steps": (
            "Restrict inbound access to trusted IP ranges instead of 0.0.0.0/0."
        ),
    },
    {
        "rule_id": "CIS-AWS-003",
        "cis_control_id": "1.16",
        "nist_id": "PR.AC-4",
        "remediation_steps": (
            "Replace wildcard actions with specific actions following the "
            "principle of least privilege."
        ),
    },
    {
        "rule_id": "CIS-AWS-004",
        "cis_control_id": "2.1.1",
        "nist_id": "PR.DS-1",
        "remediation_steps": (
            "Enable default server-side encryption (SSE-S3 or SSE-KMS) on the bucket."
        ),
    },
    {
        "rule_id": "CIS-AWS-005",
        "cis_control_id": "1.16",
        "nist_id": "PR.AC-4",
        "remediation_steps": (
            "Remove wildcard principals; grant access only to specific, trusted principals."
        ),
    },
]


compliance_map = sa.table(
    "compliance_map",
    sa.column("rule_id", sa.String),
    sa.column("cis_control_id", sa.String),
    sa.column("nist_id", sa.String),
    sa.column("remediation_steps", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(compliance_map, _SEED)


def downgrade() -> None:
    rule_ids = [row["rule_id"] for row in _SEED]
    op.execute(
        compliance_map.delete().where(compliance_map.c.rule_id.in_(rule_ids))
    )
