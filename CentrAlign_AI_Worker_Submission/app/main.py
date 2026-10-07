from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import store
from .agent import run_task

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="CentrAlign AI Worker", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


class RunRequest(BaseModel):
    task: str
    auto_approve: bool = False


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return (BASE / "static" / "index.html").read_text()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/inbox", response_class=HTMLResponse)
def inbox():
    rows = "".join(
        f"<tr data-invoice data-id='{x['id']}' data-vendor='{x['vendor']}' data-date='{x['invoice_date']}' data-amount='{x['amount']}' data-due='{x['due_date']}'><td><a data-invoice-id='{x['id']}' href='/inbox/{x['id']}'>{x['id']}</a></td><td>{x['vendor']}</td><td>{x['invoice_date']}</td><td>₹{x['amount']:,.2f}</td><td>{x['due_date']}</td><td>{x['status']}</td></tr>" for x in store.INVOICES
    )
    return f"""<!doctype html><html><body><main style='font-family:Arial;margin:40px'><h1>Company Invoice Inbox</h1><table border='1' cellpadding='8'><tr><th>Invoice</th><th>Vendor</th><th>Date</th><th>Amount</th><th>Due</th><th>Status</th></tr>{rows}</table></main></body></html>"""


@app.get("/inbox/{invoice_id}", response_class=HTMLResponse)
def invoice_page(invoice_id: str):
    item = next((x for x in store.INVOICES if x["id"] == invoice_id), None)
    if not item:
        raise HTTPException(404, "Invoice not found")
    return f"""<!doctype html><html><body><main style='font-family:Arial;margin:40px'><h1>Invoice Detail</h1><p><b>Invoice ID:</b> <span data-field='invoice-id'>{item['id']}</span></p><p><b>Vendor:</b> <span data-field='vendor'>{item['vendor']}</span></p><p><b>Amount:</b> <span data-field='amount'>₹{item['amount']:,.2f}</span></p><p><b>Due date:</b> <span data-field='due-date'>{item['due_date']}</span></p><p><b>Source file:</b> {item['file']}</p><a href='/inbox'>Back</a></main></body></html>"""


@app.get("/erp/new", response_class=HTMLResponse)
def erp_new():
    return """<!doctype html><html><body><main style='font-family:Arial;margin:40px;max-width:700px'><h1>Internal Accounts Payable</h1><form method='post' action='/erp/new'><label>Vendor <input id='vendor' name='vendor'></label><br><br><label>Invoice ID <input id='invoice_id' name='invoice_id'></label><br><br><label>Amount <input id='amount' name='amount'></label><br><br><label>Due date <input id='due_date' name='due_date'></label><br><br><button type='submit'>Create payable</button></form></main></body></html>"""


@app.post("/erp/new", response_class=HTMLResponse)
async def erp_create(request: Request):
    form = await request.form()
    record_id = f"AP-{len(store.ERP_RECORDS)+1:04d}"
    row = {
        "id": record_id,
        "vendor": str(form["vendor"]),
        "invoice_id": str(form["invoice_id"]),
        "amount": float(str(form["amount"])),
        "due_date": str(form["due_date"]),
        "created": True,
    }
    store.ERP_RECORDS.append(row)
    return f"""<!doctype html><html><body><main style='font-family:Arial;margin:40px'><div data-created='true'>Payable created successfully.</div><p><b>ERP ID:</b> <span data-field='erp-id'>{record_id}</span></p><p><a href='/erp/records/{record_id}'>Open record</a></p></main></body></html>"""


@app.get("/erp/records/{record_id}", response_class=HTMLResponse)
def erp_record(record_id: str):
    item = next((x for x in store.ERP_RECORDS if x["id"] == record_id), None)
    if not item:
        raise HTTPException(404, "ERP record not found")
    return f"""<!doctype html><html><body><main style='font-family:Arial;margin:40px'><h1>Accounts Payable Record</h1><p>ERP ID: <span data-field='erp-id'>{item['id']}</span></p><p>Vendor: <span data-field='vendor'>{item['vendor']}</span></p><p>Invoice ID: <span data-field='invoice-id'>{item['invoice_id']}</span></p><p>Amount: <span data-field='amount'>₹{item['amount']:,.2f}</span></p><p>Due date: <span data-field='due-date'>{item['due_date']}</span></p></main></body></html>"""


@app.post("/api/run")
def api_run(req: RunRequest):
    if not req.task.strip():
        raise HTTPException(400, "Task is required")
    return run_task(req.task.strip(), auto_approve=req.auto_approve)


@app.post("/api/reset")
def api_reset():
    store.reset_state()
    return {"status": "reset"}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    if run_id not in store.RUNS:
        raise HTTPException(404, "Run not found")
    return JSONResponse(store.RUNS[run_id])


@app.post("/api/runs/{run_id}/approve")
def approve(run_id: str):
    if run_id not in store.RUNS:
        raise HTTPException(404, "Run not found")
    from .agent import Agent
    return Agent().approve(run_id)
