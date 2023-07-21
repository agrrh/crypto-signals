from pydantic import BaseModel

from lib.currency import Currency
from lib.taxes import Taxes


class Exchange(BaseModel):
    sell: Currency
    buy: Currency

    taxes: Taxes

    def do(self) -> Currency:
        reference_amount = self.taxes.apply(currency=self.sell) * self.sell.rate

        buy_amount = reference_amount / self.buy.rate
        self.buy.amount = self.taxes.apply(currency=Currency(code=self.buy.code, amount=buy_amount))

        return self.buy
