from pydantic import BaseModel

from lib.currency import Currency


class Taxes(BaseModel):
    relative: float = 0.0  # 0.05 means "5% of total sum"
    static: float = 0.0  # e.g. 1.0 means "1 coin per deal"

    def apply(self, currency: Currency):
        return currency.amount * (1 - self.relative) - self.static
