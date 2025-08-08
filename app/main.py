import argparse
import logging
import os
from datetime import date, datetime
from typing import List, Optional

from .classifier import apply_classification
from .config import CONFIG
from .models import CustomerDebt, Status
from .parsers.csv_reader import parse_csv
from .parsers.pdf_reader import parse_pdf
from .whatsapp import maybe_send_debt_message


def setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def load_debts_from_source(source_path: str) -> List[CustomerDebt]:
    _, ext = os.path.splitext(source_path.lower())
    if ext == ".pdf":
        return parse_pdf(source_path)
    if ext in (".csv", ".txt"):
        return parse_csv(source_path)
    raise ValueError("Formato de arquivo não suportado. Use PDF ou CSV.")


def filter_by_status(debts: List[CustomerDebt], status: Optional[str]) -> List[CustomerDebt]:
    if not status:
        return debts
    wanted = status.strip().lower()
    return [d for d in debts if (d.status or "").lower() == wanted]


def print_list(debts: List[CustomerDebt]) -> None:
    if not debts:
        print("Nenhum registro encontrado.")
        return
    header = ["Cliente", "Telefone", "Valor", "Vencimento", "Status"]
    print(" | ".join(header))
    print("-" * 80)
    for d in debts:
        amount_str = f"R$ {d.amount:.2f}".replace(".", ",", 1)
        due_str = d.due_date.strftime("%d/%m/%Y") if d.due_date else ""
        phone = d.phone or ""
        print(f"{d.client_name} | {phone} | {amount_str} | {due_str} | {d.status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cobrança automática via WhatsApp – Salomon Ltda.")
    parser.add_argument("--source", required=True, help="Caminho do arquivo PDF ou CSV exportado do ERP")
    parser.add_argument("--status", choices=[Status.EM_DIA, Status.A_PAGAR, Status.EM_DEBITO], help="Filtrar por status")
    parser.add_argument("--list", action="store_true", help="Apenas listar registros (sem enviar mensagens)")
    parser.add_argument("--send", action="store_true", help="Enviar mensagens conforme status e filtros")
    parser.add_argument("--no-dry-run", action="store_true", help="Executar envio real (por padrão, dry-run)")
    parser.add_argument("--today", help="Data base no formato dd/mm/aaaa (para testes)")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Aumenta verbosidade (-v, -vv)")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if not os.path.exists(args.source):
        raise SystemExit("Arquivo de origem não encontrado.")

    base_date: date
    if args.today:
        try:
            base_date = datetime.strptime(args.today, "%d/%m/%Y").date()
        except ValueError:
            raise SystemExit("--today deve estar em dd/mm/aaaa")
    else:
        base_date = date.today()

    debts = load_debts_from_source(args.source)
    debts = apply_classification(debts, today=base_date, due_soon_days=CONFIG.due_soon_days)
    debts = filter_by_status(debts, args.status)

    if args.list or not args.send:
        print_list(debts)

    if args.send:
        dry_run = not args.no_dry_run
        total = 0
        sent = 0
        skipped = 0
        for d in debts:
            total += 1
            result = maybe_send_debt_message(d, dry_run=dry_run)
            if result is None:
                skipped += 1
                continue
            sent += 1
        print(f"Processados: {total} | Enviados: {sent} | Ignorados: {skipped} | Dry-run: {dry_run}")


if __name__ == "__main__":
    main()