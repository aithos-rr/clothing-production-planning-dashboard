"""Central source of truth for thresholds, status labels, colors, and recommendation labels.

No threshold literal (0.85, 1.00, 0.90, etc.) should appear elsewhere in the codebase.
"""
from __future__ import annotations

# --- Utilization thresholds (PRD §8) ---
SAFE_UTILIZATION_THRESHOLD: float = 0.85
CRITICAL_UTILIZATION_THRESHOLD: float = 1.00
PHASE_STRESS_THRESHOLD: float = 0.90
MAX_PARALLEL_ORDERS_PER_LAB: int = 2

# --- Status labels ---
STATUS_SAFE: str = "safe"
STATUS_AT_RISK: str = "at_risk"
STATUS_CRITICAL: str = "critical"
STATUS_NEUTRAL: str = "neutral"

STATUS_COLORS: dict[str, str] = {
    "safe": "#22C55E",
    "at_risk": "#F59E0B",
    "critical": "#EF4444",
    "neutral": "#6B7280",
}

# --- Recommendation labels (PRD §12) ---
REC_ACCEPT: str = "ACCEPT"
REC_AT_RISK: str = "AT_RISK"
REC_REALLOCATE: str = "REALLOCATE"
REC_SPLIT: str = "SPLIT"
REC_POSTPONE: str = "POSTPONE"
REC_REJECT: str = "REJECT"

ALL_RECOMMENDATIONS: tuple[str, ...] = (
    REC_ACCEPT,
    REC_AT_RISK,
    REC_REALLOCATE,
    REC_SPLIT,
    REC_POSTPONE,
    REC_REJECT,
)

# --- Severity levels ---
SEVERITY_LOW: str = "low"
SEVERITY_MEDIUM: str = "medium"
SEVERITY_HIGH: str = "high"

# --- Stress event types (PRD §9.6) ---
EVENT_UTILIZATION_HIGH: str = "utilization_high"
EVENT_UTILIZATION_CRITICAL: str = "utilization_critical"
EVENT_PHASE_OVERLOAD: str = "phase_overload"
EVENT_OVERTIME_REQUIRED: str = "overtime_required"
EVENT_MACHINE_DOWNTIME: str = "machine_downtime"
EVENT_WORKER_ABSENCE: str = "worker_absence"
EVENT_PARALLEL_OVERLOAD: str = "parallel_overload"
EVENT_DEADLINE_INFEASIBLE: str = "deadline_infeasible"

# --- Timeline status values ---
TIMELINE_ON_TRACK: str = "on_track"
TIMELINE_AT_RISK: str = "at_risk"
TIMELINE_LATE: str = "late"
TIMELINE_BLOCKED: str = "blocked"  # a required phase has no defined capacity
