from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx

from .config import MODEL_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL


@dataclass
class Plan:
    goal: str
    vendor: str
    actions: list[dict[str, Any]]
    approval_required: bool = False


VENDOR_ALIASES = {
    "acme": "Acme Corporation",
    "acme corporation": "Acme Corporation",
    "zenith": "Zenith Systems",
    "zenith systems": "Zenith Systems",
}


def extract_vendor(task: str) -> str:
    lower = task.lower()
    for alias, canonical in VENDOR_ALIASES.items():
        if alias in lower:
            return canonical
    m = re.search(r"from\s+([A-Za-z0-9 .&_-]+?)(?:,|\s+extract|\s+and\s+enter|\s+and\s+tell|$)", task, re.I)
    if m:
        return m.group(1).strip().title()
    raise ValueError("I couldn't identify the vendor in the request.")


def _understand_local(task: str) -> dict[str, Any]:
    lower = task.lower()
    vendor = extract_vendor(task)
    return {
        "intent": "process_latest_invoice",
        "vendor": vendor,
        "needs_latest": "latest" in lower or "most recent" in lower,
        "extract_amount": "amount" in lower,
        "extract_due_date": "due date" in lower or "duedate" in lower,
        "enter_internal_system": any(x in lower for x in ["enter", "internal system", "erp", "accounts payable"]),
        "report_completion": any(x in lower for x in ["tell me", "report", "once it is done", "done"]),
    }


def understand(task: str) -> dict[str, Any]:
    if MODEL_PROVIDER.lower() != "openai" or not OPENAI_API_KEY:
        return _understand_local(task)

    prompt = (
        "Extract the user's business outcome into JSON with keys: intent, vendor, "
        "needs_latest, extract_amount, extract_due_date, enter_internal_system, report_completion. "
        "Only intent=process_latest_invoice is supported. Do not invent data.\n\n" + task
    )
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": OPENAI_MODEL,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are a structured task-understanding component for a safe enterprise automation agent."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=15,
        )
        response.raise_for_status()
        import json
        parsed = json.loads(response.json()["choices"][0]["message"]["content"])
        if parsed.get("intent") != "process_latest_invoice" or not parsed.get("vendor"):
            raise ValueError("Unsupported or incomplete LLM plan")
        return parsed
    except Exception:
        return _understand_local(task)


def make_plan(task: str, approval_threshold: float) -> Plan:
    ctx = understand(task)
    if ctx["intent"] != "process_latest_invoice":
        raise ValueError("This prototype currently supports invoice-processing tasks.")
    actions = [
        {"id": "open_inbox", "tool": "browser", "description": "Open the company invoice inbox."},
        {"id": "find_invoice", "tool": "browser", "description": f"Find the latest invoice from {ctx['vendor']}."},
        {"id": "extract_fields", "tool": "browser", "description": "Read the invoice amount and due date from the invoice page."},
        {"id": "approval_check", "tool": "policy", "description": "Check whether the invoice requires human approval."},
        {"id": "enter_erp", "tool": "browser", "description": "Create the payable record in the simulated ERP."},
        {"id": "verify", "tool": "browser", "description": "Re-open the ERP record and verify amount, due date, vendor, and invoice id."},
        {"id": "summarize", "tool": "agent", "description": "Return concise evidence of completion."},
    ]
    return Plan(goal=f"Process the latest invoice from {ctx['vendor']}", vendor=ctx["vendor"], actions=actions)
