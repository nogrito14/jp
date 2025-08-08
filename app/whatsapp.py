import json
import logging
from typing import Optional

import requests

from .config import CONFIG
from .models import CustomerDebt, Status
from .utils import normalize_phone_to_e164

logger = logging.getLogger(__name__)


def build_message_text(debt: CustomerDebt) -> Optional[str]:
    if debt.status == Status.EM_DIA:
        return None
    if debt.status == Status.A_PAGAR:
        return (
            f"Olá {debt.client_name}, aqui é da {CONFIG.officina_name}.\n"
            f"Notamos que o serviço realizado tem vencimento em {debt.due_date:%d/%m/%Y}.\n"
            f"Valor: R$ {debt.amount:.2f}.\n"
            f"Pedimos a gentileza de efetuar o pagamento até a data.\n"
            f"Em caso de dúvidas, fale conosco: {CONFIG.officina_wa_link or CONFIG.officina_phone}"
        )
    if debt.status == Status.EM_DEBITO:
        return (
            f"Olá {debt.client_name}, aqui é da {CONFIG.officina_name}.\n"
            f"Identificamos um débito vencido em {debt.due_date:%d/%m/%Y}.\n"
            f"Valor pendente: R$ {debt.amount:.2f}.\n"
            f"Por favor, regularize o pagamento.\n"
            f"Fale conosco: {CONFIG.officina_wa_link or CONFIG.officina_phone}"
        )
    return None


def send_whatsapp_text(to_phone: str, text: str, token: Optional[str] = None, phone_number_id: Optional[str] = None) -> dict:
    api_token = token or CONFIG.whatsapp_token
    phone_id = phone_number_id or CONFIG.whatsapp_phone_number_id
    if not api_token or not phone_id:
        raise RuntimeError("Credenciais do WhatsApp Business API não configuradas.")

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
    try:
        data = response.json()
    except Exception:
        data = {"text": response.text}

    if response.status_code >= 400:
        logger.error("Erro WhatsApp API: %s", data)
    return {"status_code": response.status_code, "data": data}


def maybe_send_debt_message(debt: CustomerDebt, dry_run: bool = True) -> Optional[dict]:
    message = build_message_text(debt)
    if not message:
        return None

    e164 = normalize_phone_to_e164(debt.phone, CONFIG.default_country_code)
    if not e164:
        logger.warning("Telefone ausente ou inválido para %s", debt.client_name)
        return None

    if dry_run:
        logger.info("[dry-run] Enviaria para %s: %s", e164, message)
        return {"dry_run": True, "to": e164, "message": message}

    return send_whatsapp_text(e164, message)