import logging
import os
import sys

from lib.provider import Provider
from lib.manager import Manager
from lib.wallet import Wallet
from lib.currency import Currency
from lib.taxes import Taxes
from lib.tg_notifier import TGNotifier


PREFERENCES = {
    "USDT": 0,
    "BNB": 75,
    "ETH": 50,
    "XRP": 50,
    "ADA": 50,
    "SOL": 50,
    "DOGE": 50,
    "TRX": 50,
    "MATIC": 50,
    "LTC": 50,
    "DOT": 50,
    "AVAX": 50,
    "WBTC": 50,
    "BCH": 50,
}


def main():
    provider = Provider()

    manager = Manager(provider=provider, preferences=PREFERENCES)
    notifier = TGNotifier(
        token=os.environ.get("APP_TG_TOKEN"),
        chat_id=os.environ.get("APP_TG_CHAT_ID"),
    )

    w_actual = Wallet(currencies={k: Currency(code=k) for k in PREFERENCES.keys()})
    w_actual.currencies.get("USDT").amount = 100.0

    ok = manager.update_rates(currency_list=w_actual.currencies.keys())
    if not ok:
        logging.error("could not get rates initially")
        sys.exit()

    w_reference = manager.generate_reference_wallet(wallet=w_actual)

    taxes_null = Taxes()

    logging.info("starting observation loop")
    notifier.send("starting observation loop")

    while True:
        ok = manager.update_rates(currency_list=w_actual.currencies.keys())

        if ok:
            good_exchanges = manager.get_good_exchanges(
                wallet_actual=w_actual, wallet_reference=w_reference, taxes=taxes_null
            )
            exchange = manager.choose_exchange(exchanges=good_exchanges)
            notifier.send_exchanges(exchange=exchange, exchanges=good_exchanges)

        logging.debug("waiting before next iteration")
        manager.take_a_break()


if __name__ == "__main__":
    logging.critical("starting application")
    main()
