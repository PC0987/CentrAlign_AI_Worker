from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

INVOICES = [
    {
        "id": "INV-ACME-1002",
        "vendor": "Acme Corporation",
        "invoice_date": "2026-10-07",
        "amount": 4820.00,
        "due_date": "2026-11-06",
        "file": "acme_october_1002.pdf",
        "status": "unprocessed",
    },
    {
        "id": "INV-ACME-1001",
        "vendor": "Acme Corporation",
        "invoice_date": "2026-09-12",
        "amount": 4210.00,
        "due_date": "2026-10-12",
        "file": "acme_september_1001.pdf",
        "status": "unprocessed",
    },
    {
        "id": "INV-ZENITH-883",
        "vendor": "Zenith Systems",
        "invoice_date": "2026-10-05",
        "amount": 14850.00,
        "due_date": "2026-11-04",
        "file": "zenith_october_883.pdf",
        "status": "unprocessed",
    },
]

ERP_RECORDS: list[dict[str, Any]] = []
RUNS: dict[str, dict[str, Any]] = {}


def reset_state() -> None:
    global INVOICES, ERP_RECORDS, RUNS
    INVOICES = deepcopy([
        {
            "id": "INV-ACME-1002",
            "vendor": "Acme Corporation",
            "invoice_date": "2026-10-07",
            "amount": 4820.00,
            "due_date": "2026-11-06",
            "file": "acme_october_1002.pdf",
            "status": "unprocessed",
        },
        {
            "id": "INV-ACME-1001",
            "vendor": "Acme Corporation",
            "invoice_date": "2026-09-12",
            "amount": 4210.00,
            "due_date": "2026-10-12",
            "file": "acme_september_1001.pdf",
            "status": "unprocessed",
        },
        {
            "id": "INV-ZENITH-883",
            "vendor": "Zenith Systems",
            "invoice_date": "2026-10-05",
            "amount": 14850.00,
            "due_date": "2026-11-04",
            "file": "zenith_october_883.pdf",
            "status": "unprocessed",
        },
    ])
    ERP_RECORDS = []
    RUNS = {}
