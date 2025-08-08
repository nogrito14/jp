from __future__ import annotations

import os
import tempfile
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .classifier import apply_classification
from .config import CONFIG
from .models import CustomerDebt, Status
from .parsers.csv_reader import parse_csv
from .parsers.pdf_reader import parse_pdf
from .whatsapp import maybe_send_debt_message

app = FastAPI(title="Cobrança Salomon – Web")

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# In-memory store of last import
LAST_DEBTS: List[CustomerDebt] = []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    has_data = len(LAST_DEBTS) > 0
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "has_data": has_data,
            "due_soon_days": CONFIG.due_soon_days,
            "officina_name": CONFIG.officina_name,
        },
    )


@app.post("/import", response_class=HTMLResponse)
async def import_file(request: Request, file: UploadFile = File(...)):
    global LAST_DEBTS
    suffix = os.path.splitext(file.filename or "")[1].lower()
    if suffix not in {".pdf", ".csv"}:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Apenas PDF ou CSV.", "has_data": len(LAST_DEBTS) > 0},
            status_code=400,
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            debts = parse_pdf(tmp_path)
        else:
            debts = parse_csv(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    LAST_DEBTS = apply_classification(debts, today=date.today(), due_soon_days=CONFIG.due_soon_days)
    return RedirectResponse(url="/preview", status_code=303)


@app.get("/preview", response_class=HTMLResponse)
async def preview(request: Request, status: Optional[str] = None):
    debts = LAST_DEBTS
    if status:
        debts = [d for d in debts if d.status == status]
    return templates.TemplateResponse(
        "preview.html",
        {
            "request": request,
            "debts": debts,
            "status": status,
            "statuses": [Status.EM_DIA, Status.A_PAGAR, Status.EM_DEBITO],
        },
    )


@app.post("/send", response_class=HTMLResponse)
async def send_messages(
    request: Request,
    status: str = Form(...),
    dry_run: Optional[str] = Form(None),
):
    selected = [d for d in LAST_DEBTS if d.status == status]
    is_dry_run = dry_run is not None
    total = len(selected)
    sent = 0
    skipped = 0
    results = []
    for d in selected:
        result = maybe_send_debt_message(d, dry_run=is_dry_run)
        if result is None:
            skipped += 1
        else:
            sent += 1
            results.append(result)

    return templates.TemplateResponse(
        "send_result.html",
        {
            "request": request,
            "total": total,
            "sent": sent,
            "skipped": skipped,
            "dry_run": is_dry_run,
            "status": status,
        },
    )