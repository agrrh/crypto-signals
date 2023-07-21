import time
import logging

from pydantic import BaseModel
from typing import ClassVar, Dict, List

from lib.provider import Provider
from lib.wallet import Wallet
from lib.currency import Currency
from lib.exchange import Exchange
from lib.taxes import Taxes


class Manager(BaseModel):
    break_duration: ClassVar[int] = 60
    good_deal_ratio: ClassVar[float] = 0.01

    provider: Provider
    preferences: Dict[str, float]

    rates: ClassVar[Dict[str, float]] = {
        "USDT": 1.0,
    }

    def __update_wallet_rates(self, wallet: Wallet) -> Wallet:
        for code in wallet.currencies.keys():
            if not self.rates.get(code):
                logging.warning(f'no rate present for {code}')

            wallet.currencies.get(code).rate = self.rates.get(code)
        return wallet

    def __get_reference_amount(self, currency: Currency) -> float:
        return currency.amount * self.rates.get(currency.code)

    def __apply_exchange(self, wallet: Wallet, exchange: Exchange) -> Wallet:
        wallet = self.__update_wallet_rates(wallet)

        wallet.currencies.get(exchange.sell.code).amount = 0.0
        wallet.currencies.get(exchange.buy.code).amount += exchange.do().amount

        return wallet

    def generate_reference_wallet(self, wallet: Wallet) -> Wallet:
        wallet = self.__update_wallet_rates(wallet)
        ref_wallet = self.__update_wallet_rates(wallet)

        taxes = Taxes()

        for code, currency in wallet.currencies.items():
            if code == "USDT":
                continue

            ref_wallet.currencies[code] = Exchange(
                sell=ref_wallet.currencies.get("USDT"),
                buy=currency,
                taxes=taxes,
            ).do()

        return ref_wallet

    def update_rates(self, currency_list: list):
        try:
            rates = self.provider.get_rates(currency_list=currency_list)
        except Exception as e:
            logging.warning(f"could not update rates, skipping: {e}")
            return False

        self.rates.update(rates)
        return True

    def get_good_exchanges(self, wallet_actual: Wallet, wallet_reference: Wallet, taxes: Taxes) -> List[Exchange]:
        wallet_actual = self.__update_wallet_rates(wallet_actual)
        wallet_reference = self.__update_wallet_rates(wallet_reference)

        reference_amounts = {
            code: self.__get_reference_amount(currency) for code, currency in wallet_actual.currencies.items()
        }
        currency_to_sell = max(reference_amounts, key=reference_amounts.get)
        currency_to_sell = wallet_actual.currencies.get(currency_to_sell)

        possible_exchanges = [
            Exchange(
                sell=currency_to_sell,
                buy=currency,
                taxes=taxes,
            )
            for currency in wallet_actual.currencies.values()
            if currency != currency_to_sell
        ]

        good_exchanges = []

        for exchange in possible_exchanges:
            wallet_tmp = wallet_actual

            wallet_tmp = self.__apply_exchange(wallet=wallet_tmp, exchange=exchange)

            result_amount = wallet_tmp.currencies.get(exchange.buy.code).amount
            wanted_amount = wallet_reference.currencies.get(exchange.buy.code).amount * (
                1.0 + self.good_deal_ratio
            )

            logging.info(f'inspecting deal: {exchange}')

            if result_amount > wanted_amount and result_amount > 0:
                logging.warning(f'possibly good deal: {exchange}')
                good_exchanges.append(exchange)

        return good_exchanges

    def choose_exchange(self, exchanges: List[Exchange]) -> Exchange:
        if len(exchanges) == 0:
            return None

        exchanges_weighted = {}

        for exchange in exchanges:
            code = exchange.buy.code
            value = exchange.buy.reference_amount * self.preferences.get(code) / sum(self.preferences.values())

            exchanges_weighted[code] = value

        top_exchange = max(exchanges_weighted, exchanges_weighted.get)

        return top_exchange

    def take_a_break(self):
        time.sleep(self.break_duration)
