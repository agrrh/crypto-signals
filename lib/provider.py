import requests
import logging

from pydantic import BaseModel
from typing import ClassVar, Dict


class Provider(BaseModel):
    metrics_url: ClassVar[str] = "https://prometheus.agrrh.com/api/v1/query"
    reference_currency: ClassVar[str] = "USDT"

    def __call(self, currency: str) -> float:
        metrics_query = (
            f'sum(exchange_rate{{currency=~"{currency}",reference_currency="{self.reference_currency}"}}) by (currency)'
        )

        try:
            resp = requests.get(
                self.metrics_url,
                params={
                    "query": metrics_query,
                },
            )
            data = resp.json()
        except Exception as e:
            logging.warning(f"could not get data from provider: {e}")

        try:
            assert data.get("status") == "success"
            assert data.get("data").get("resultType") == "vector"

            rates = {
                vector.get("metric").get("currency"): float(vector.get("value")[1])
                for vector in data.get("data").get("result")
            }
        except Exception as e:
            logging.warning(f"could not get data from provider: {e}")

        return rates

    def get_rates(self, currency_list: list) -> Dict[str, float]:
        currency = "|".join(currency_list)

        return self.__call(currency=currency)
