from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


class Status:
    EM_DIA = "em_dia"
    A_PAGAR = "a_pagar"
    EM_DEBITO = "em_debito"


@dataclass
class CustomerDebt:
    client_name: str
    cpf: Optional[str]
    phone: Optional[str]
    amount: Decimal
    service_date: Optional[date]
    due_date: date
    status: Optional[str] = None