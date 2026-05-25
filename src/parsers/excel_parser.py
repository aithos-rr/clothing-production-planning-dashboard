"""Pure-IO Excel reader.

Returns raw DataFrames keyed by sheet name. No business logic, no normalization.
"""
from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Union

import pandas as pd

PathLike = Union[str, Path, BinaryIO]


class ExcelParseError(Exception):
    """Raised when the uploaded file cannot be opened as an .xlsx workbook."""


def _coerce_path(file: PathLike) -> PathLike:
    """Return a usable handle. Strings/Path checked for extension; file-likes pass through."""
    if isinstance(file, (str, Path)):
        p = Path(file)
        if p.suffix.lower() not in {".xlsx", ".xlsm"}:
            raise ExcelParseError(
                f"Unsupported file type: {p.suffix or '<no extension>'}. Expected .xlsx."
            )
        if not p.exists():
            raise ExcelParseError(f"File not found: {p}")
        return p
    return file


def list_sheets(file: PathLike) -> list[str]:
    """Return the ordered list of sheet names in the workbook."""
    f = _coerce_path(file)
    try:
        xl = pd.ExcelFile(f, engine="openpyxl")
        return list(xl.sheet_names)
    except ExcelParseError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ExcelParseError(f"Failed to open workbook: {exc}") from exc


def parse_excel(file: PathLike) -> dict[str, pd.DataFrame]:
    """Read every sheet of the workbook into a raw DataFrame.

    Returns: `{sheet_name: dataframe}`. No normalization.
    Raises: `ExcelParseError` on unsupported / unreadable / empty workbook.
    """
    f = _coerce_path(file)
    try:
        raw = pd.read_excel(f, sheet_name=None, engine="openpyxl")
    except ExcelParseError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ExcelParseError(f"Failed to parse workbook: {exc}") from exc
    if not raw:
        raise ExcelParseError("Workbook contains no sheets.")
    return raw


__all__ = ["parse_excel", "list_sheets", "ExcelParseError"]
