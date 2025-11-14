from pydantic import Field
from app.core.config.base import EnvBaseSettings


class InvoiceSettings(EnvBaseSettings):
    COMPANY_NAME: str = Field(..., description="Company name")
    COMPANY_PHONE: str = Field(..., description="Company phone number")
    COMPANY_EMAIL: str = Field(..., description="Company email address")
