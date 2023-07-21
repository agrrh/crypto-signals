from pydantic import BaseModel
from typing import List

import requests

from lib.exchange import Exchange


class TGNotifier(BaseModel):
    token: str
    chat_id: str

    def __tg_api_call(self, text: str):
        url_req = (
            "https://api.telegram.org/bot" + self.token + "/sendMessage" + "?chat_id=" + self.chat_id + "&text=" + text
        )
        results = requests.get(url_req)
        return results.json()

    def send(self, exchange: Exchange, exchanges: List[Exchange]) -> None:
        if not exchange:
            return None

        text = ""
        text += "\n".join([e for e in exchanges if e != exchange])
        text += "\n"
        text += exchange

        return self.__tg_api_call(text)
