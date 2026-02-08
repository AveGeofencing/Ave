from abc import ABC
from enum import StrEnum
from pydantic import BaseModel


# Email message schemas
class BaseEmail(BaseModel, ABC):
    """
    All default values. Contains metadata for the emails being sent.
    """

    subject: str | None = "[Ave] Welcome to Ave"
    template_path: str = "base.html"
    context_vars: dict
