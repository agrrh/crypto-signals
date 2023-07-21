from pydantic import BaseModel
from typing import Dict

from lib.currency import Currency


class Wallet(BaseModel):
    currencies: Dict[str, Currency]
