"""
Database Models (SQLModel).

Tables (matching docs/schema.md):
- users
- scans
- findings
- compliance_map
- audit_log

NOTE (fix): this module intentionally does NOT use
``from __future__ import annotations``. Combined with SQLModel's
``Relationship(List["X"])`` declarations, PEP 563 stringized annotations break
SQLAlchemy 2.x mapper initialization ("seems to be using a generic class as the
argument to relationship()"). Keeping runtime annotations lets the mappers
resolve ``List["Scan"]`` etc. correctly.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp (replaces the deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


# ==========================================================
# ENUMS  (labels follow docs/schema.md)
# ==========================================================

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"


class ScanType(str, Enum):
    STATIC = "STATIC"
    LIVE = "LIVE"


class ScanStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Severity(str, Enum):
    # Title-case VALUES are intentional: the Phase 1 rule engine emits
    # "High"/"Critical"/... (from the rule YAML), so these values let the
    # engine output validate straight into the model/schema.
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# ==========================================================
# USERS
# ==========================================================

class User(SQLModel, table=True):
    __tablename__ = "users"

    user_id: UUID = Field(default_factory=uuid4, primary_key=True)

    email: str = Field(index=True, unique=True)
    password_hash: str

    role: UserRole = Field(default=UserRole.VIEWER)

    created_at: datetime = Field(default_factory=_utcnow)

    scans: List["Scan"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")


# ==========================================================
# SCANS
# ==========================================================

class Scan(SQLModel, table=True):
    __tablename__ = "scans"

    scan_id: UUID = Field(default_factory=uuid4, primary_key=True)

    user_id: UUID = Field(foreign_key="users.user_id", index=True)

    # Additive (not in schema.md, required by the API/UI): original upload name.
    filename: str

    scan_type: ScanType = Field(default=ScanType.STATIC)
    status: ScanStatus = Field(default=ScanStatus.IN_PROGRESS)

    timestamp: datetime = Field(default_factory=_utcnow)

    user: Optional["User"] = Relationship(back_populates="scans")
    findings: List["Finding"] = Relationship(back_populates="scan")


# ==========================================================
# COMPLIANCE MAP
# ==========================================================

class ComplianceMap(SQLModel, table=True):
    __tablename__ = "compliance_map"

    rule_id: str = Field(primary_key=True)

    cis_control_id: str
    nist_id: str
    remediation_steps: str

    findings: List["Finding"] = Relationship(back_populates="compliance")


# ==========================================================
# FINDINGS
# ==========================================================

class Finding(SQLModel, table=True):
    __tablename__ = "findings"

    finding_id: UUID = Field(default_factory=uuid4, primary_key=True)

    scan_id: UUID = Field(foreign_key="scans.scan_id", index=True)

    resource_id: str
    resource_type: str
    severity: Severity

    rule_id: str = Field(foreign_key="compliance_map.rule_id", index=True)

    # Additive (not in schema.md): human-readable remediation/explanation text
    # produced by the Phase 1 rule engine.
    message: str

    risk_score: Optional[int] = Field(default=None)
    is_anomaly: bool = Field(default=False)

    created_at: datetime = Field(default_factory=_utcnow)

    scan: Optional["Scan"] = Relationship(back_populates="findings")
    compliance: Optional["ComplianceMap"] = Relationship(back_populates="findings")


# ==========================================================
# AUDIT LOG
# ==========================================================

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    event_id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Nullable per contract (system events may have no associated user).
    user_id: Optional[UUID] = Field(
        default=None, foreign_key="users.user_id", index=True
    )

    action: str

    # INET in Postgres; stored as text for cross-database (SQLite dev) support.
    ip_address: Optional[str] = Field(default=None)

    timestamp: datetime = Field(default_factory=_utcnow)

    user: Optional["User"] = Relationship(back_populates="audit_logs")
