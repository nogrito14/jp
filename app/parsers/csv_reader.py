import csv
from datetime import date
from decimal import Decimal
from typing import List

from ..models import CustomerDebt
from ..utils import parse_brazilian_date, parse_currency_to_decimal


def parse_csv(path: str) -> List[CustomerDebt]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    debts: List[CustomerDebt] = []
    for r in rows:
        name = (r.get("Nome") or r.get("Cliente") or r.get("name") or "").strip()
        if not name:
            continue
        cpf = (r.get("CPF") or r.get("CNPJ") or r.get("cpf") or r.get("cnpj") or None)
        phone = (r.get("Telefone") or r.get("Celular") or r.get("Fone") or r.get("WhatsApp") or r.get("phone") or None)
        amount = parse_currency_to_decimal(r.get("Valor") or r.get("Total") or r.get("amount") or "0")
        service_date = parse_brazilian_date(r.get("DataServico") or r.get("Emissao") or r.get("service_date") or "")
        due_date = parse_brazilian_date(r.get("Vencimento") or r.get("due_date") or "")
        if not due_date:
            continue
        debts.append(
            CustomerDebt(
                client_name=name,
                cpf=cpf,
                phone=phone,
                amount=amount,
                service_date=service_date,
                due_date=due_date,
            )
        )
    return debts