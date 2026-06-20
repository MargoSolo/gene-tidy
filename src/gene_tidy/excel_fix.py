"""Detect and recover Excel date-corrupted gene symbols.

Microsoft Excel (and other spreadsheet tools) auto-convert some gene symbols
into dates the moment a file is opened:

    SEPT2  -> "2-Sep"    (septins)
    MARCH1 -> "1-Mar"    (membrane-associated RING-CH / MARCHF)
    MARC1  -> "1-Mar"    (mitochondrial amidoxime reducing component / MTARC)
    DEC1   -> "1-Dec"

This module spots the date-shaped strings and proposes the gene symbol(s)
they most likely came from. It NEVER resolves on its own and NEVER guesses
silently -- it just returns candidate symbols and always sets a warning so the
caller can flag the row. Where a corrupted form is genuinely ambiguous (e.g.
"1-Mar" -> MARCH1 or MARC1) it returns *all* candidates.

Note: numeric Excel date *serials* (e.g. ``44075``) are indistinguishable from
Entrez gene IDs and are intentionally NOT reinterpreted here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Month token (abbreviation or full name) -> gene-symbol prefix(es).
# A month mapping to several prefixes means the recovered symbol is ambiguous.
_MONTH_TO_PREFIXES = {
    "sep": ["SEPT"],
    "sept": ["SEPT"],
    "september": ["SEPT"],
    "mar": ["MARCH", "MARC"],
    "march": ["MARCH", "MARC"],
    "dec": ["DEC"],
    "december": ["DEC"],
}

# day-month  e.g. "2-Sep", "02/Sep", "1 March", optionally a trailing year.
_DAY_MONTH = re.compile(
    r"^(\d{1,2})[-/ ]([A-Za-z]{3,9})(?:[-/ ]\d{2,4})?$"
)
# month-day  e.g. "Sep-2", "Sep/02", "March 1", optionally a trailing year.
_MONTH_DAY = re.compile(
    r"^([A-Za-z]{3,9})[-/ ](\d{1,2})(?:[-/ ]\d{2,4})?$"
)


@dataclass
class ExcelFixResult:
    """Outcome of inspecting one value for Excel date corruption."""

    is_corrupted: bool
    candidates: List[str] = field(default_factory=list)
    warning: str = ""

    @property
    def is_ambiguous(self) -> bool:
        return len(self.candidates) > 1


def _candidates_for(month_token: str, number: str) -> List[str]:
    prefixes = _MONTH_TO_PREFIXES.get(month_token.lower())
    if not prefixes:
        return []
    n = int(number)  # strips a leading zero, e.g. "02" -> 2
    if n < 1:
        return []
    return [f"{prefix}{n}" for prefix in prefixes]


def detect_excel_corruption(value) -> Optional[ExcelFixResult]:
    """Inspect a single value for Excel date corruption.

    Returns ``None`` when the value does not look like a date-corrupted gene
    symbol. Otherwise returns an :class:`ExcelFixResult` whose ``candidates``
    are the gene symbols the value most likely originated from (possibly more
    than one, when ambiguous).
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    month = None
    number = None

    m = _DAY_MONTH.match(s)
    if m:
        number, month = m.group(1), m.group(2)
    else:
        m = _MONTH_DAY.match(s)
        if m:
            month, number = m.group(1), m.group(2)

    if month is None:
        return None

    candidates = _candidates_for(month, number)
    if not candidates:
        # Looked date-shaped but the month maps to no known gene family
        # (e.g. "2-Apr"); not a known corruption -> leave it alone.
        return None

    if len(candidates) == 1:
        warning = (
            f"Excel date-corruption detected ('{s}'); "
            f"recovered candidate symbol {candidates[0]}"
        )
    else:
        warning = (
            f"Excel date-corruption detected ('{s}'); "
            f"ambiguous between {', '.join(candidates)}"
        )

    return ExcelFixResult(is_corrupted=True, candidates=candidates,
                          warning=warning)


def looks_excel_corrupted(value) -> bool:
    """True if the value looks like an Excel date-corrupted gene symbol."""
    return detect_excel_corruption(value) is not None
