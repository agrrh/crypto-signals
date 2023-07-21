from pydantic import BaseModel


class Currency(BaseModel):
    code: str
    amount: float = 0.0
    rate: float = 0.0

    @property
    def reference_amount(self) -> float:
        return self.amount * self.rate

    def add(self, amount: float) -> float:
        self.amount += amount
        return self.amount
