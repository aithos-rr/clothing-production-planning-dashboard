"""Convert raw Excel sheets into canonical DataFrames per PRD §7.

Each `normalize_*` function returns `(df, warnings)`. The orchestrator
`normalize_all` runs all four and substitutes sample data when sheets are
missing (Mode B from PRD §6.2).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from src.parsers.excel_parser import parse_excel
from src.utils.config import get_default
from src.utils.constants import SEVERITY_HIGH, SEVERITY_LOW, SEVERITY_MEDIUM
from src.utils.validation import (
    ValidationWarning,
    check_required_columns,
)

# Italian → canonical English aliases (case-insensitive)
_COLUMN_ALIASES: dict[str, str] = {
    "cliente": "client",
    "quantita": "quantity",
    "quantità": "quantity",
    "scadenza": "deadline",
    "data_inizio": "start_date",
    "data_fine": "end_date",
    "tipo_prodotto": "product_type",
    "ordine": "order_id",
    "laboratorio": "assigned_lab",
    "catena": "assigned_chain",
    "priorita": "priority",
    "priorità": "priority",
    "fase": "phase_name",
    "tempo_medio": "avg_time_minutes",
    "tempo_min": "min_time_minutes",
    "tempo_max": "max_time_minutes",
    "tempo_setup": "setup_time_minutes",
    "ordine_fase": "phase_order",
    "operai": "workers_total",
    "operai_assegnati": "workers_assigned",
    "macchine": "machines_total",
    "efficienza": "efficiency",
    "uptime_macchine": "uptime",
}

SAMPLE_PATH = Path("data/sample/sample_planning.xlsx")

# Canonical schemas (used to enforce column order on output)
ORDERS_COLS = [
    "order_id", "client", "product_type", "quantity",
    "start_date", "deadline", "assigned_lab", "assigned_chain",
    "progress_percentage", "priority",
]
PRODUCT_MATRIX_COLS = [
    "product_type", "phase_name", "min_time_minutes", "max_time_minutes",
    "avg_time_minutes", "setup_time_minutes", "phase_order",
]
LABS_COLS = [
    "lab_id", "lab_name", "working_hours_per_day", "working_days_per_week",
    "default_efficiency", "machine_uptime", "max_weekly_hours", "overtime_allowed",
]
PHASE_CAPACITY_COLS = [
    "lab_id", "phase_name", "workers_total", "workers_assigned",
    "machines_total", "available_minutes_per_day", "efficiency", "uptime",
]


def _canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names and apply Italian aliases."""
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    renamed = {}
    for c in df.columns:
        key = str(c).strip().lower().replace(" ", "_")
        renamed[c] = _COLUMN_ALIASES.get(key, key)
    return df.rename(columns=renamed)


def _to_date_series(s: pd.Series) -> pd.Series:
    """Coerce a series to `datetime.date`; bad parses become pd.NaT then None."""
    parsed = pd.to_datetime(s, errors="coerce")
    return parsed.dt.date.where(parsed.notna(), None)


# ---------- TASK-011 ----------
def normalize_orders(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationWarning]]:
    """Normalize the `orders` sheet into PRD §7.1 schema.

    Note: `progress_percentage` uses the fraction scale [0.0, 1.0] throughout.
    """
    warnings: list[ValidationWarning] = []
    df = _canonicalize_columns(raw_df).copy() if raw_df is not None else pd.DataFrame()

    if df.empty:
        warnings.append(ValidationWarning("orders", "Orders sheet is empty.", SEVERITY_HIGH))
        return pd.DataFrame(columns=ORDERS_COLS), warnings

    # Required columns
    warnings.extend(check_required_columns(df, ["product_type", "quantity", "deadline"], "orders"))

    # Generate order_id if missing
    if "order_id" not in df.columns or df["order_id"].isna().all():
        df["order_id"] = [f"ORD-{i:04d}" for i in range(1, len(df) + 1)]
    else:
        # Fill nulls with generated ids
        mask = df["order_id"].isna()
        if mask.any():
            df.loc[mask, "order_id"] = [f"ORD-{i:04d}" for i in df.index[mask] + 1]

    # Fallbacks per PRD §7.1
    if "client" not in df.columns:
        df["client"] = "Unknown Client"
    else:
        df["client"] = df["client"].fillna("Unknown Client")

    if "start_date" not in df.columns:
        df["start_date"] = date.today()
    if "deadline" not in df.columns:
        df["deadline"] = pd.NaT  # will yield None below
    if "assigned_lab" not in df.columns:
        df["assigned_lab"] = "Default Lab"
    else:
        df["assigned_lab"] = df["assigned_lab"].fillna("Default Lab")
    if "assigned_chain" not in df.columns:
        df["assigned_chain"] = "Default Chain"
    else:
        df["assigned_chain"] = df["assigned_chain"].fillna("Default Chain")
    if "progress_percentage" not in df.columns:
        df["progress_percentage"] = 0.0
    else:
        df["progress_percentage"] = pd.to_numeric(df["progress_percentage"], errors="coerce").fillna(0.0)
        # If user supplied 0..100 scale, normalize to 0..1
        if df["progress_percentage"].max() > 1.5:
            df["progress_percentage"] = df["progress_percentage"] / 100.0
    if "priority" not in df.columns:
        df["priority"] = "normal"
    else:
        df["priority"] = df["priority"].fillna("normal")

    if "product_type" not in df.columns:
        df["product_type"] = None  # already warned above
    if "quantity" not in df.columns:
        df["quantity"] = 0

    # Casts
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
    df["start_date"] = _to_date_series(df["start_date"])
    df["deadline"] = _to_date_series(df["deadline"])
    df["progress_percentage"] = df["progress_percentage"].astype(float).clip(0.0, 1.0)

    return df.reindex(columns=ORDERS_COLS), warnings


# ---------- TASK-012 ----------
def normalize_product_matrix(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationWarning]]:
    """Normalize the `product_matrix` sheet into PRD §7.2 schema."""
    warnings: list[ValidationWarning] = []
    df = _canonicalize_columns(raw_df).copy() if raw_df is not None else pd.DataFrame()

    if df.empty:
        warnings.append(ValidationWarning("product_matrix", "Product matrix sheet is empty.", SEVERITY_HIGH))
        return pd.DataFrame(columns=PRODUCT_MATRIX_COLS), warnings

    warnings.extend(check_required_columns(df, ["product_type", "phase_name"], "product_matrix"))

    # Ensure numeric columns (force float64 so empty-mask assignments don't
    # trip pandas' LossySetitem guard on object/NA-dtyped columns).
    for col in ("min_time_minutes", "max_time_minutes", "avg_time_minutes", "setup_time_minutes"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
        else:
            df[col] = pd.Series([float("nan")] * len(df), dtype="float64", index=df.index)

    # Compute avg from min/max if missing (PRD §7.2 fallback)
    has_min = df["min_time_minutes"].notna()
    has_max = df["max_time_minutes"].notna()
    has_avg = df["avg_time_minutes"].notna()

    mask_min_max = ~has_avg & has_min & has_max
    if mask_min_max.any():
        df.loc[mask_min_max, "avg_time_minutes"] = (
            df.loc[mask_min_max, "min_time_minutes"] + df.loc[mask_min_max, "max_time_minutes"]
        ) / 2.0

    mask_only_min = ~has_avg & has_min & ~has_max
    if mask_only_min.any():
        df.loc[mask_only_min, "avg_time_minutes"] = df.loc[mask_only_min, "min_time_minutes"]

    mask_only_max = ~has_avg & ~has_min & has_max
    if mask_only_max.any():
        df.loc[mask_only_max, "avg_time_minutes"] = df.loc[mask_only_max, "max_time_minutes"]

    # Rows still missing avg → high warning
    still_missing = df["avg_time_minutes"].isna()
    if still_missing.any():
        for idx in df.index[still_missing]:
            phase = df.at[idx, "phase_name"] if "phase_name" in df.columns else "?"
            warnings.append(
                ValidationWarning(
                    "avg_time_minutes",
                    f"Cannot determine avg_time_minutes for product_matrix row idx={idx} (phase={phase}).",
                    SEVERITY_HIGH,
                )
            )

    df["setup_time_minutes"] = df["setup_time_minutes"].fillna(0.0).astype(float)

    # Phase order: infer if missing
    if "phase_order" not in df.columns:
        df["phase_order"] = pd.NA
    df["phase_order"] = pd.to_numeric(df["phase_order"], errors="coerce")
    if df["phase_order"].isna().any() and "product_type" in df.columns:
        # Where missing, use cumcount within product_type
        missing_mask = df["phase_order"].isna()
        cum = df.groupby("product_type").cumcount() + 1
        df.loc[missing_mask, "phase_order"] = cum.loc[missing_mask]
    df["phase_order"] = df["phase_order"].fillna(1).astype(int)

    df["avg_time_minutes"] = df["avg_time_minutes"].astype(float)

    return df.reindex(columns=PRODUCT_MATRIX_COLS), warnings


# ---------- TASK-013 ----------
def normalize_labs(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, list[ValidationWarning]]:
    """Normalize the `labs` sheet into PRD §7.3 schema."""
    warnings: list[ValidationWarning] = []
    df = _canonicalize_columns(raw_df).copy() if raw_df is not None else pd.DataFrame()

    if df.empty:
        warnings.append(ValidationWarning("labs", "Labs sheet is empty.", SEVERITY_HIGH))
        return pd.DataFrame(columns=LABS_COLS), warnings

    warnings.extend(check_required_columns(df, ["lab_id"], "labs"))

    # Optional columns filled from config defaults
    defaults = {
        "working_hours_per_day": float(get_default("working_hours_per_day")),
        "working_days_per_week": int(get_default("working_days_per_week")),
        "default_efficiency": float(get_default("default_efficiency")),
        "machine_uptime": float(get_default("machine_uptime")),
        "max_weekly_hours": float(get_default("max_weekly_hours")),
        "overtime_allowed": bool(get_default("overtime_allowed")),
    }

    if "lab_id" not in df.columns:
        df["lab_id"] = [f"LAB-{i:02d}" for i in range(1, len(df) + 1)]
    if "lab_name" not in df.columns:
        df["lab_name"] = df["lab_id"]
    else:
        df["lab_name"] = df["lab_name"].fillna(df["lab_id"])

    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val
        else:
            df[col] = df[col].where(df[col].notna(), val)

    # Casts
    for col in ("working_hours_per_day", "default_efficiency", "machine_uptime", "max_weekly_hours"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(defaults[col]).astype(float)
    df["working_days_per_week"] = pd.to_numeric(df["working_days_per_week"], errors="coerce").fillna(
        defaults["working_days_per_week"]
    ).astype(int)
    df["overtime_allowed"] = df["overtime_allowed"].astype(bool)

    return df.reindex(columns=LABS_COLS), warnings


# ---------- TASK-014 ----------
def normalize_phase_capacity(
    raw_df: pd.DataFrame,
    labs_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[ValidationWarning]]:
    """Normalize the `phase_capacity` sheet into PRD §7.4 schema.

    Computes `available_minutes_per_day` from
        workers_assigned × (lab.working_hours_per_day × 60) × efficiency × uptime
    """
    warnings: list[ValidationWarning] = []
    df = _canonicalize_columns(raw_df).copy() if raw_df is not None else pd.DataFrame()

    if df.empty:
        warnings.append(ValidationWarning("phase_capacity", "Phase capacity sheet is empty.", SEVERITY_HIGH))
        return pd.DataFrame(columns=PHASE_CAPACITY_COLS), warnings

    warnings.extend(check_required_columns(df, ["lab_id", "phase_name", "workers_total"], "phase_capacity"))

    # Index labs by id for fast lookup
    lab_lookup = labs_df.set_index("lab_id").to_dict("index") if not labs_df.empty else {}

    if "workers_total" not in df.columns:
        df["workers_total"] = 1
    df["workers_total"] = pd.to_numeric(df["workers_total"], errors="coerce").fillna(1).astype(int)

    if "workers_assigned" not in df.columns:
        df["workers_assigned"] = df["workers_total"]
    else:
        df["workers_assigned"] = pd.to_numeric(df["workers_assigned"], errors="coerce").fillna(df["workers_total"]).astype(int)

    if "machines_total" not in df.columns:
        df["machines_total"] = 0
    df["machines_total"] = pd.to_numeric(df["machines_total"], errors="coerce").fillna(0).astype(int)

    # Fill efficiency / uptime from matching lab when missing
    if "efficiency" not in df.columns:
        df["efficiency"] = pd.NA
    if "uptime" not in df.columns:
        df["uptime"] = pd.NA

    eff_filled: list[float] = []
    upt_filled: list[float] = []
    hours_per_day: list[float] = []
    for _, row in df.iterrows():
        lab_id = row.get("lab_id")
        lab = lab_lookup.get(lab_id)
        if lab is None:
            warnings.append(
                ValidationWarning(
                    "lab_id",
                    f"Phase capacity row references unknown lab_id='{lab_id}'.",
                    SEVERITY_HIGH,
                )
            )
            eff_default = float(get_default("default_efficiency"))
            upt_default = float(get_default("machine_uptime"))
            hpd_default = float(get_default("working_hours_per_day"))
            eff_filled.append(eff_default if pd.isna(row.get("efficiency")) else float(row["efficiency"]))
            upt_filled.append(upt_default if pd.isna(row.get("uptime")) else float(row["uptime"]))
            hours_per_day.append(hpd_default)
        else:
            eff_filled.append(
                float(lab.get("default_efficiency", get_default("default_efficiency")))
                if pd.isna(row.get("efficiency"))
                else float(row["efficiency"])
            )
            upt_filled.append(
                float(lab.get("machine_uptime", get_default("machine_uptime")))
                if pd.isna(row.get("uptime"))
                else float(row["uptime"])
            )
            hours_per_day.append(float(lab.get("working_hours_per_day", get_default("working_hours_per_day"))))

    df["efficiency"] = eff_filled
    df["uptime"] = upt_filled
    available = [
        wa * (hpd * 60.0) * eff * upt
        for wa, hpd, eff, upt in zip(df["workers_assigned"], hours_per_day, df["efficiency"], df["uptime"])
    ]
    df["available_minutes_per_day"] = available

    return df.reindex(columns=PHASE_CAPACITY_COLS), warnings


# ---------- TASK-015 ----------
def _empty_sheet(df: pd.DataFrame | None) -> bool:
    return df is None or df.empty


def _load_sample_sheets() -> dict[str, pd.DataFrame]:
    if not SAMPLE_PATH.exists():
        return {}
    try:
        return parse_excel(SAMPLE_PATH)
    except Exception:  # noqa: BLE001
        return {}


def normalize_all(
    raw: dict[str, pd.DataFrame],
    use_mock_fallback: bool = True,
) -> dict:
    """Run all four normalizers; substitute sample sheets where input is missing/empty.

    Returns dict with keys: orders, product_matrix, labs, phase_capacity,
    warnings (list), used_mock (dict[str, bool]).
    """
    raw = raw or {}
    sample = _load_sample_sheets() if use_mock_fallback else {}
    used_mock: dict[str, bool] = {k: False for k in ("orders", "product_matrix", "labs", "phase_capacity")}

    def pick(name: str) -> pd.DataFrame:
        df = raw.get(name)
        if _empty_sheet(df) and use_mock_fallback and not _empty_sheet(sample.get(name)):
            used_mock[name] = True
            return sample[name]
        return df if df is not None else pd.DataFrame()

    warnings: list[ValidationWarning] = []

    orders_df, w = normalize_orders(pick("orders"))
    warnings.extend(w)
    pm_df, w = normalize_product_matrix(pick("product_matrix"))
    warnings.extend(w)
    labs_df, w = normalize_labs(pick("labs"))
    warnings.extend(w)
    pc_df, w = normalize_phase_capacity(pick("phase_capacity"), labs_df)
    warnings.extend(w)

    return {
        "orders": orders_df,
        "product_matrix": pm_df,
        "labs": labs_df,
        "phase_capacity": pc_df,
        "warnings": warnings,
        "used_mock": used_mock,
    }


__all__ = [
    "normalize_orders",
    "normalize_product_matrix",
    "normalize_labs",
    "normalize_phase_capacity",
    "normalize_all",
    "ORDERS_COLS",
    "PRODUCT_MATRIX_COLS",
    "LABS_COLS",
    "PHASE_CAPACITY_COLS",
]
