from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

import pdfplumber

from ..models import CustomerDebt
from ..utils import parse_brazilian_date, parse_currency_to_decimal

logger = logging.getLogger(__name__)


HEADER_ALIASES = {
    "client_name": {"cliente", "nome", "nome do cliente", "razao social"},
    "cpf": {"cpf", "cpf/cnpj", "cnpj"},
    "phone": {"telefone", "celular", "fone", "whatsapp"},
    "amount": {"valor", "valor devido", "total", "valor total"},
    "service_date": {"data servico", "data do servico", "data serviço", "emissao", "data"},
    "due_date": {"vencimento", "data vencimento", "dt venc"},
}


def _normalize_header(h: str) -> str:
    return h.strip().lower()


def _map_header_indices(headers: List[str]) -> Dict[str, int]:
    norm = [_normalize_header(h) for h in headers]
    mapping: Dict[str, int] = {}
    for field, aliases in HEADER_ALIASES.items():
        for i, h in enumerate(norm):
            if h in aliases:
                mapping[field] = i
                break
    return mapping


def _row_to_debt(row: List[str], mapping: Dict[str, int]) -> Optional[CustomerDebt]:
    try:
        name = row[mapping["client_name"]].strip()
        cpf = row[mapping["cpf"]].strip() if "cpf" in mapping else None
        phone = row[mapping["phone"]].strip() if "phone" in mapping else None
        amount_text = row[mapping["amount"]]
        amount: Decimal = parse_currency_to_decimal(amount_text)
        service_date = parse_brazilian_date(row[mapping["service_date"]]) if "service_date" in mapping else None
        due_date = parse_brazilian_date(row[mapping["due_date"]])
        if not name or not due_date:
            return None
        return CustomerDebt(
            client_name=name,
            cpf=cpf,
            phone=phone,
            amount=amount,
            service_date=service_date,
            due_date=due_date,
        )
    except Exception as exc:
        logger.debug("Falha ao converter linha para dívida: %s", exc)
        return None


def parse_pdf(path: str) -> List[CustomerDebt]:
    debts: List[CustomerDebt] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
            except Exception as exc:
                logger.warning("Falha ao extrair tabelas: %s", exc)
                continue
            for table in tables or []:
                if not table or len(table) < 2:
                    continue
                headers = [str(cell or "").strip() for cell in table[0]]
                mapping = _map_header_indices(headers)
                if "client_name" not in mapping or "amount" not in mapping or "due_date" not in mapping:
                    continue
                for raw_row in table[1:]:
                    row = [str(cell or "").strip() for cell in raw_row]
                    debt = _row_to_debt(row, mapping)
                    if debt:
                        debts.append(debt)
    return debts