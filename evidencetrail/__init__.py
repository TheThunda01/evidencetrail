"""EvidenceTrail: transparent checks for research extraction tables."""

__version__ = "0.1.0"

from .audit import (
    CHECKED_RULES,
    EVIDENCE_STATUSES,
    FINDING_COLUMNS,
    REQUIRED_COLUMNS,
    REVIEW_STATUSES,
    AuditResult,
    Finding,
    audit_table,
)

__all__ = [
    "__version__",
    "CHECKED_RULES",
    "EVIDENCE_STATUSES",
    "FINDING_COLUMNS",
    "REQUIRED_COLUMNS",
    "REVIEW_STATUSES",
    "AuditResult",
    "Finding",
    "audit_table",
]
