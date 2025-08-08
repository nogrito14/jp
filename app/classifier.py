from datetime import date
from typing import List

from .models import CustomerDebt, Status


def classify_debt(debt: CustomerDebt, today: date, due_soon_days: int) -> str:
    if debt.due_date < today:
        return Status.EM_DEBITO
    days_until_due = (debt.due_date - today).days
    if 0 <= days_until_due <= due_soon_days:
        return Status.A_PAGAR
    return Status.EM_DIA


def apply_classification(debts: List[CustomerDebt], today: date, due_soon_days: int) -> List[CustomerDebt]:
    for d in debts:
        d.status = classify_debt(d, today=today, due_soon_days=due_soon_days)
    return debts