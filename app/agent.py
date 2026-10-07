from __future__ import annotations

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .config import APPROVAL_THRESHOLD, SANDBOX_FILE
from .planner import make_plan
from . import store


class Agent:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def log(self, stage: str, message: str, **data: Any) -> None:
        event = {"ts": datetime.utcnow().isoformat() + "Z", "stage": stage, "message": message}
        if data:
            event["data"] = data
        self.events.append(event)

    def run(self, task: str, auto_approve: bool = False, existing_run: dict[str, Any] | None = None) -> dict[str, Any]:
        run_id = existing_run["id"] if existing_run else f"run-{uuid.uuid4().hex[:10]}"
        started = time.time()
        record = existing_run or {"id": run_id, "task": task, "status": "running", "events": self.events, "result": None}
        record["status"] = "running"
        record["events"] = self.events
        store.RUNS[run_id] = record
        if existing_run is None:
            self.log("understand", "Interpreting the user's intended outcome.")
            try:
                plan = make_plan(task, APPROVAL_THRESHOLD)
                self.log("plan", "Generated an executable plan.", plan=[a["id"] for a in plan.actions])
            except Exception as exc:
                record["status"] = "failed"; record["result"] = {"error": str(exc)}; return record
        else:
            self.log("human", "Approval received; resuming the existing run.")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox", "--disable-gpu"])
                context = browser.new_context()
                page = context.new_page()
                try:
                    invoice = self._find_latest_invoice(page, make_plan(task, APPROVAL_THRESHOLD).vendor)
                    self.log("observe", "Located invoice.", invoice=invoice)
                    self._extract_invoice(page, invoice)
                    self.log("observe", "Extracted invoice fields from the rendered page.", amount=invoice["amount"], due_date=invoice["due_date"])

                    if invoice["amount"] >= APPROVAL_THRESHOLD and not auto_approve:
                        record["status"] = "awaiting_approval"
                        record["result"] = {"invoice": invoice, "reason": f"Amount ₹{invoice['amount']:.2f} exceeds approval threshold ₹{APPROVAL_THRESHOLD:.2f}."}
                        self.log("human", "Paused before the consequential action and requested human approval.")
                        return record

                    erp_id = self._enter_erp(page, invoice)
                    self.log("execute", "Created ERP payable record.", erp_id=erp_id)
                    verified = self._verify(page, erp_id, invoice)
                    if not verified:
                        raise RuntimeError("Verification failed: ERP record did not match the invoice.")
                    self.log("verify", "Verified the requested outcome with an independent re-read.", erp_id=erp_id)
                    record["status"] = "completed"
                    record["result"] = {
                        "invoice": invoice,
                        "erp_record_id": erp_id,
                        "evidence": {"invoice": f"file://{Path(SANDBOX_FILE).resolve()}#invoice/{invoice['id']}", "erp": f"file://{Path(SANDBOX_FILE).resolve()}#erp/{erp_id}"},
                    }
                    self.log("complete", "Task completed with evidence.")
                    return record
                finally:
                    context.close(); browser.close()
        except Exception as exc:
            self.log("recover", "Execution failed; classified the failure explicitly.", error=str(exc))
            record["status"] = "failed"; record["result"] = {"error": str(exc)}; return record
        finally:
            record["duration_ms"] = round((time.time() - started) * 1000, 1)
            store.RUNS[run_id] = record

    def approve(self, run_id: str) -> dict[str, Any]:
        run = store.RUNS[run_id]
        if run["status"] != "awaiting_approval":
            return run
        self.events = run["events"]
        return self.run(run["task"], auto_approve=True, existing_run=run)

    def _load_sandbox(self, page, route: str = "inbox") -> None:
        page.set_content(Path(SANDBOX_FILE).read_text(encoding="utf-8"), wait_until="domcontentloaded")
        page.evaluate("route => { location.hash = route; }", route)
        page.wait_for_timeout(50)

    def _find_latest_invoice(self, page, vendor: str) -> dict[str, Any]:
        self.log("execute", "Opening the company invoice inbox in a real browser.")
        self._load_sandbox(page, "inbox")
        rows = page.locator("[data-invoice]")
        candidates = []
        for i in range(rows.count()):
            row = rows.nth(i)
            if row.get_attribute("data-vendor") == vendor:
                candidates.append({"id": row.get_attribute("data-id"), "invoice_date": row.get_attribute("data-date"), "amount": float(row.get_attribute("data-amount")), "vendor": vendor, "due_date": row.get_attribute("data-due")})
        if not candidates:
            raise RuntimeError(f"No invoice found for {vendor}.")
        candidates.sort(key=lambda x: x["invoice_date"], reverse=True)
        latest = candidates[0]
        try:
            page.get_by_role("link", name=latest["id"]).click(timeout=1500)
        except PlaywrightTimeoutError:
            self.log("recover", "Primary invoice locator failed; using a DOM fallback locator.")
            page.locator(f"a[data-invoice-id='{latest['id']}']").click()
        return latest

    def _extract_invoice(self, page, invoice: dict[str, Any]) -> None:
        page.wait_for_selector("[data-field='invoice-id']")
        invoice["id"] = page.locator("[data-field='invoice-id']").inner_text().strip()
        invoice["vendor"] = page.locator("[data-field='vendor']").inner_text().strip()
        invoice["amount"] = float(page.locator("[data-field='amount']").inner_text().replace(",", "").replace("₹", "").strip())
        invoice["due_date"] = page.locator("[data-field='due-date']").inner_text().strip()

    def _enter_erp(self, page, invoice: dict[str, Any]) -> str:
        page.evaluate("location.hash = 'erp-new'")
        page.wait_for_timeout(50)
        page.locator("#vendor").fill(invoice["vendor"])
        page.locator("#invoice_id").fill(invoice["id"])
        page.locator("#amount").fill(str(invoice["amount"]))
        page.locator("#due_date").fill(invoice["due_date"])
        page.get_by_role("button", name="Create payable").click()
        page.wait_for_selector("[data-created='true']")
        return page.locator("[data-field='erp-id']").inner_text().strip()

    def _verify(self, page, erp_id: str, invoice: dict[str, Any]) -> bool:
        page.evaluate("id => { location.hash = 'erp/' + id; }", erp_id)
        page.wait_for_timeout(50)
        observed = {
            "vendor": page.locator("[data-field='vendor']").inner_text().strip(),
            "invoice_id": page.locator("[data-field='invoice-id']").inner_text().strip(),
            "amount": float(page.locator("[data-field='amount']").inner_text().replace(",", "").replace("₹", "").strip()),
            "due_date": page.locator("[data-field='due-date']").inner_text().strip(),
        }
        return observed["vendor"] == invoice["vendor"] and observed["invoice_id"] == invoice["id"] and abs(observed["amount"] - float(invoice["amount"])) < 0.01 and observed["due_date"] == invoice["due_date"]


def run_task(task: str, auto_approve: bool = False) -> dict[str, Any]:
    agent = Agent()
    return agent.run(task, auto_approve=auto_approve)
