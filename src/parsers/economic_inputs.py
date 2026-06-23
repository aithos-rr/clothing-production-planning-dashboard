"""Economic input sourcing (PRD v2 §5/§6).

Sources per-lab hourly cost & overtime multiplier, per-product overhead %,
and per-order setup cost from an `economic_layer` sheet when present; otherwise
falls back to config defaults (flagged via `uses_default`). No numeric literals:
every fallback comes from config/defaults.yaml.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.utils.config import get_default

_ECON_SHEET_NAMES = ("economic_layer", "economic", "economics")


@dataclass
class EconomicInputs:
    _hourly: dict[str, float] = field(default_factory=dict)
    _overtime: dict[str, float] = field(default_factory=dict)
    _overhead: dict[str, float] = field(default_factory=dict)
    _setup: dict[str, float] = field(default_factory=dict)
    _smv: dict[str, float] = field(default_factory=dict)
    uses_default: bool = True

    # Config fallbacks (read once)
    _def_hourly: float = field(default_factory=lambda: float(get_default("standard_hourly_cost")))
    _def_overtime: float = field(default_factory=lambda: float(get_default("overtime_multiplier")))
    _def_overhead: float = field(default_factory=lambda: float(get_default("overhead_percentage")))
    _def_setup: float = field(default_factory=lambda: float(get_default("fixed_setup_cost")))

    def hourly_cost(self, lab_id) -> float:
        return float(self._hourly.get(str(lab_id), self._def_hourly))

    def overtime_multiplier(self, lab_id) -> float:
        return float(self._overtime.get(str(lab_id), self._def_overtime))

    def overhead_pct(self, product_type) -> float:
        return float(self._overhead.get(str(product_type), self._def_overhead))

    def setup_cost(self, order_id) -> float:
        return float(self._setup.get(str(order_id), self._def_setup))

    def smv(self, order_id) -> float | None:
        """Standard minutes per garment for an order, or None if not provided.

        When present, the economic engine derives required_hours as
        `quantity * smv / 60` (the apparel-standard costing basis, which
        reconciles with the source workbook), instead of summing per-phase times.
        """
        return self._smv.get(str(order_id))


def _find_econ_sheet(raw: dict[str, pd.DataFrame]) -> pd.DataFrame | None:
    if not raw:
        return None
    for k, v in raw.items():
        if str(k).strip().lower() in _ECON_SHEET_NAMES and v is not None and not v.empty:
            return v
    return None


def load_economic_inputs(raw: dict[str, pd.DataFrame]) -> EconomicInputs:
    sheet = _find_econ_sheet(raw)
    if sheet is None:
        return EconomicInputs(uses_default=True)

    df = sheet.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]

    hourly: dict[str, float] = {}
    overtime: dict[str, float] = {}
    overhead: dict[str, float] = {}
    setup: dict[str, float] = {}
    smv: dict[str, float] = {}

    def _num(v):
        try:
            f = float(v)
            return f if pd.notna(f) else None
        except (TypeError, ValueError):
            return None

    for _, row in df.iterrows():
        lab = row.get("assigned_lab")
        if lab is not None and pd.notna(lab):
            hc = _num(row.get("standard_hourly_cost_eur"))
            if hc is not None:
                hourly[str(lab)] = hc
            ot = _num(row.get("overtime_multiplier"))
            if ot is not None:
                overtime[str(lab)] = ot
        # Alternative lab cost columns extend lab coverage
        alt = row.get("alternative_lab")
        if alt is not None and pd.notna(alt):
            ahc = _num(row.get("alternative_hourly_cost_eur"))
            if ahc is not None:
                hourly.setdefault(str(alt), ahc)
        prod = row.get("product_type")
        if prod is not None and pd.notna(prod):
            oh = _num(row.get("overhead_pct"))
            if oh is not None:
                overhead[str(prod)] = oh
        oid = row.get("order_id")
        if oid is not None and pd.notna(oid):
            sc = _num(row.get("setup_cost_eur"))
            if sc is not None:
                setup[str(oid)] = sc
            sv = _num(row.get("planned_smv"))
            if sv is not None and sv > 0:
                smv[str(oid)] = sv

    sourced = bool(hourly or overtime or overhead or setup)
    return EconomicInputs(
        _hourly=hourly,
        _overtime=overtime,
        _overhead=overhead,
        _setup=setup,
        _smv=smv,
        uses_default=not sourced,
    )


__all__ = ["EconomicInputs", "load_economic_inputs"]
