"""Generate `data/sample/sample_planning.xlsx` with the four canonical sheets.

Run: `python scripts/build_sample_data.py`
Requires: openpyxl (listed in requirements.txt).

Produces a small but realistic dataset:
  - 5 orders covering 2 product types ("Giacca", "Pantalone"); one tight-deadline order.
  - 2 product types × 4 phases each in the product_matrix.
  - 2 labs (L1, L2).
  - 8 phase_capacity rows (2 labs × 4 phases).
  - At least one order designed to exceed lab daily capacity so bottleneck logic has a target.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook

OUTPUT = Path("data/sample/sample_planning.xlsx")
TODAY = date(2026, 5, 25)


def _orders_rows() -> list[list]:
    header = [
        "order_id", "client", "product_type", "quantity",
        "start_date", "deadline", "assigned_lab", "assigned_chain",
        "progress_percentage", "priority",
    ]
    rows: list[list] = [
        ["ORD-0001", "Atelier Roma",     "Giacca",    120, TODAY,                    TODAY + timedelta(days=14), "L1", "Chain-A", 0.0, "normal"],
        ["ORD-0002", "Boutique Milano",  "Pantalone", 200, TODAY,                    TODAY + timedelta(days=10), "L1", "Chain-A", 0.1, "normal"],
        ["ORD-0003", "Studio Firenze",   "Giacca",    600, TODAY,                    TODAY + timedelta(days=12), "L2", "Chain-B", 0.0, "normal"],  # designed to overload
        ["ORD-0004", "House Torino",     "Pantalone", 80,  TODAY + timedelta(days=2), TODAY + timedelta(days=20), "L2", "Chain-B", 0.0, "low"],
        ["ORD-0005", "Maison Venezia",   "Giacca",    150, TODAY,                    TODAY + timedelta(days=4),  "L1", "Chain-A", 0.0, "urgent"],  # tight deadline
    ]
    return [header] + rows


def _product_matrix_rows() -> list[list]:
    header = [
        "product_type", "phase_name", "min_time_minutes", "max_time_minutes",
        "avg_time_minutes", "setup_time_minutes", "phase_order",
    ]
    rows: list[list] = [
        ["Giacca", "imbastitura",     8.0,  12.0, 10.0, 2.0, 1],
        ["Giacca", "rifilo",          4.0,  6.0,  5.0,  1.0, 2],
        ["Giacca", "confezione capo", 15.0, 22.0, 18.0, 3.0, 3],
        ["Giacca", "controllo misure", 2.0, 4.0,  3.0,  0.5, 4],
        ["Pantalone", "imbastitura",     5.0,  9.0,  7.0,  1.5, 1],
        ["Pantalone", "rifilo",          3.0,  5.0,  4.0,  1.0, 2],
        ["Pantalone", "confezione capo", 10.0, 16.0, 13.0, 2.5, 3],
        ["Pantalone", "controllo misure", 2.0, 3.0,  2.5,  0.5, 4],
    ]
    return [header] + rows


def _labs_rows() -> list[list]:
    header = [
        "lab_id", "lab_name", "working_hours_per_day", "working_days_per_week",
        "default_efficiency", "machine_uptime", "max_weekly_hours", "overtime_allowed",
    ]
    rows: list[list] = [
        ["L1", "Laboratorio Nord", 8, 5, 0.80, 0.92, 48, False],
        ["L2", "Laboratorio Sud",  8, 5, 0.75, 0.88, 48, False],
    ]
    return [header] + rows


def _phase_capacity_rows() -> list[list]:
    header = [
        "lab_id", "phase_name", "workers_total", "workers_assigned",
        "machines_total", "available_minutes_per_day", "efficiency", "uptime",
    ]
    # available_minutes_per_day will be recomputed by the normalizer; we still
    # pre-fill it so the raw sheet looks realistic.
    rows: list[list] = [
        ["L1", "imbastitura",      4, 4, 2, 1413.12, 0.80, 0.92],
        ["L1", "rifilo",           3, 3, 2, 1059.84, 0.80, 0.92],
        ["L1", "confezione capo",  6, 5, 4, 1766.40, 0.80, 0.92],
        ["L1", "controllo misure", 2, 2, 0, 706.56,  0.80, 0.92],
        ["L2", "imbastitura",      3, 3, 2, 950.40,  0.75, 0.88],
        ["L2", "rifilo",           2, 2, 1, 633.60,  0.75, 0.88],
        ["L2", "confezione capo",  4, 4, 3, 1267.20, 0.75, 0.88],
        ["L2", "controllo misure", 2, 1, 0, 316.80,  0.75, 0.88],
    ]
    return [header] + rows


def _economic_layer_rows() -> list[list]:
    # Per-lab hourly cost & overtime multiplier; per-product overhead %; per-order setup.
    # Derived demo values (L1 cheaper than L2 for Giacca-heavy load; differentiated).
    header = [
        "order_id", "assigned_lab", "product_type",
        "standard_hourly_cost_eur", "overtime_multiplier",
        "overhead_pct", "setup_cost_eur",
    ]
    rows: list[list] = [
        ["ORD-0001", "L1", "Giacca",    18.0, 1.25, 0.10, 120.0],
        ["ORD-0002", "L1", "Pantalone", 18.0, 1.25, 0.12,  80.0],
        ["ORD-0003", "L2", "Giacca",    21.5, 1.30, 0.10, 150.0],
        ["ORD-0004", "L2", "Pantalone", 21.5, 1.30, 0.12,  60.0],
        ["ORD-0005", "L1", "Giacca",    18.0, 1.25, 0.10, 100.0],
    ]
    return [header] + rows


def build_workbook(out_path: Path = OUTPUT) -> Path:
    wb = Workbook()
    # Default sheet → rename to "orders"
    ws = wb.active
    ws.title = "orders"
    for r in _orders_rows():
        ws.append(r)

    for name, rows in (
        ("product_matrix", _product_matrix_rows()),
        ("labs",            _labs_rows()),
        ("phase_capacity",  _phase_capacity_rows()),
        ("economic_layer",  _economic_layer_rows()),
    ):
        ws = wb.create_sheet(name)
        for r in rows:
            ws.append(r)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


if __name__ == "__main__":
    path = build_workbook()
    print(f"Wrote {path}")
