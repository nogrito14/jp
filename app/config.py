import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    whatsapp_token: str = os.getenv("WHATSAPP_TOKEN", "")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

    officina_name: str = os.getenv("OFFICINA_NAME", "Salomon Ltda.")
    officina_phone: str = os.getenv("OFFICINA_PHONE", "")
    officina_wa_link: str = os.getenv("OFFICINA_WA_LINK", "")

    default_country_code: str = os.getenv("DEFAULT_COUNTRY_CODE", "55")
    due_soon_days: int = int(os.getenv("DUE_SOON_DAYS", "7"))


CONFIG = AppConfig()