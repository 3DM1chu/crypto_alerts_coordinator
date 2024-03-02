import asyncio
import json
import multiprocessing
import os.path
import threading
from datetime import datetime, timedelta, time
from multiprocessing import Process
from typing import List
import requests
import uvicorn
from decouple import config
from fastapi import FastAPI, Request
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import declarative_base, mapped_column, relationship, Mapped, sessionmaker

TELEGRAM_TOKEN = config("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")

MINIMUM_PRICE_CHANGE_TO_ALERT_5M = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_5M"))
MINIMUM_PRICE_CHANGE_TO_ALERT_15M = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_15M"))
MINIMUM_PRICE_CHANGE_TO_ALERT_1H = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_1H"))
MINIMUM_PRICE_CHANGE_TO_ALERT_4H = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_4H"))
MINIMUM_PRICE_CHANGE_TO_ALERT_8H = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_8H"))
MINIMUM_PRICE_CHANGE_TO_ALERT_24H = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_24H"))
MINIMUM_PRICE_CHANGE_TO_ALERT_7D = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_7D"))
MINIMUM_PRICE_CHANGE_TO_ALERT_30D = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_30D"))

PORT_TO_RUN_UVICORN = int(config("PORT_TO_RUN_UVICORN"))

Base = declarative_base()


def sendTelegramNotification(notification: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={notification}"
    requests.get(url).json()


class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True)


class TokenPrice(BaseModel):
    __tablename__ = "token_prices"

    token_id: Mapped[int] = mapped_column(Integer, ForeignKey("tokens.id"))
    #token: Mapped[Token] = relationship(back_populates="token_prices")
    price = Column(Float)
    datetime = Column(String)

    def getDateTime(self):
        return datetime.strptime(str(self.datetime), "%Y-%m-%d %H:%M:%S")


class Token(BaseModel):
    __tablename__ = "tokens"

    symbol = Column(String)
    currency = Column(String, default="USD")
    token_prices: Mapped[List[TokenPrice]] = relationship()

    def getCurrentPrice(self):
        if len(self.token_prices) == 0:
            return 0.0
        return self.token_prices[-1].price

    def getCurrentPriceDatetime(self):
        if len(self.token_prices) == 0:
            return datetime.now()
        return self.token_prices[-1]

    def addPriceEntry(self, price: float, _timestamp: datetime):
        if self.getCurrentPrice() == price:
            return
        new_token_price = TokenPrice(price=price, timestamp=_timestamp)
        self.token_prices.append(new_token_price)
        session.add(new_token_price)
        self.checkIfPriceChanged(time_frame={"minutes": 5},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_5M)
        self.checkIfPriceChanged(time_frame={"minutes": 15},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_15M)
        self.checkIfPriceChanged(time_frame={"hours": 1},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_1H)
        self.checkIfPriceChanged(time_frame={"hours": 4},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_4H)
        self.checkIfPriceChanged(time_frame={"hours": 8},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_8H)
        self.checkIfPriceChanged(time_frame={"hours": 24},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_24H)
        self.checkIfPriceChanged(time_frame={"days": 7},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_24H)
        self.checkIfPriceChanged(time_frame={"days": 30},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_24H)

    def getNearestPriceEntryToTimeframe(self, time_frame):
        # Parse current datetime
        current_datetime = datetime.now()

        # Initialize variables to store the closest entry and its difference
        closest_entry = None
        closest_difference = timedelta.max  # Initialize with a large value

        # Define the timedelta object
        time_delta = timedelta(**time_frame)

        # Get the reference time by subtracting the time delta from the current datetime
        reference_time = current_datetime - time_delta

        # Iterate through each entry in price history
        for entry in self.token_prices:
            # Calculate the difference between the timestamp and the current time
            time_difference = abs(entry.timestamp - reference_time)

            # Check if the current entry is closer than the current closest entry
            if time_difference < closest_difference:
                closest_entry = entry
                closest_difference = time_difference

        return closest_entry

    def checkIfPriceChanged(self, time_frame, min_price_change_percent: float):
        # print(f"{self.getCurrentPrice()} | {len(self.price_history)}")
        historic_price_obj = self.getNearestPriceEntryToTimeframe(time_frame)
        historic_price = historic_price_obj.price
        historic_price_timestamp = historic_price_obj.timestamp

        ATH_ATL = self.checkIfPriceWasATHorATL(time_frame)
        wasATH = ATH_ATL["wasATH"]
        wasATL = ATH_ATL["wasATL"]
        if self.getCurrentPrice() > historic_price and wasATH:
            price_change = (self.getCurrentPrice() / historic_price * 100) - 100
            price_change = float("{:.3f}".format(price_change))
            notification = (f"======================\n"
                            f"{self.symbol}\n"
                            f"💹{price_change}%\n"
                            f"{self.getCurrentPrice()}$\n"
                            f"ATH in {time_frame}\n"
                            f"since {historic_price_timestamp}\n"
                            f"======================")
            if price_change >= min_price_change_percent:
                sendTelegramNotification(notification)
        elif self.getCurrentPrice() < historic_price and wasATL:
            price_change = 100 - (self.getCurrentPrice() / historic_price * 100)
            price_change = float("{:.3f}".format(price_change))
            notification = (f"======================\n"
                            f"{self.symbol}\n"
                            f"📉{price_change}%\n"
                            f"{self.getCurrentPrice()}$\n"
                            f"ATL in {time_frame}\n"
                            f"since {historic_price_timestamp}\n"
                            f"======================")
            if price_change >= min_price_change_percent:
                sendTelegramNotification(notification)
        else:
            price_change = 100 - (self.getCurrentPrice() / historic_price * 100)
            price_change = float("{:.3f}".format(price_change))
            notification = (f"======================\n"
                            f"{self.symbol}\n"
                            f"📉{price_change}%\n"
                            f"{self.getCurrentPrice()}$\n"
                            f"timeframe: {time_frame}\n"
                            f"since {historic_price_timestamp}\n"
                            f"======================")
            if price_change >= min_price_change_percent:
                print(notification)

    def checkIfPriceWasATHorATL(self, time_delta):
        # Define the time threshold (1 hour)
        time_threshold = timedelta(**time_delta)

        result = {
            "wasATH": True,
            "wasATL": True
        }

        # Iterate over price history
        for entry in self.token_prices:
            # Check if the timestamp is within the time threshold
            if datetime.now() - entry.timestamp < time_threshold:
                # Check if the price has changed
                if entry.price > self.getCurrentPrice():
                    result["wasATH"] = False
                elif entry.price < self.getCurrentPrice():
                    result["wasATL"] = False
        return result


def getIndexOfCoin(coin_symbol: str):
    id: int = 0
    for entry in tokens:
        if entry.symbol == coin_symbol:
            return id
        id += 1
    return -1


async def startPollingEndpoints(_endpoints):
    while True:
        for endpoint in _endpoints:
            for token_in_endpoint in endpoint["tokens"]:
                try:
                    requests.put(endpoint["url"] + token_in_endpoint)
                    # print("Connected to endpoint: " + endpoint["url"])
                except:
                    x = ""
        await asyncio.sleep(120)


def setup_endpoints(_endpoints):
    coins_to_check = json.loads(open("coins.json", "r").read())
    _endpoints.append({"url": "http://frog01.mikr.us:21591/putToken/", "tokens":
                      [coin_from_file["symbol"] for coin_from_file in coins_to_check]})
    asyncio.run(startPollingEndpoints(_endpoints))


app = FastAPI()


@app.post("/addTokenPrice")
async def addTokenToCheck(request: Request):
    json_data = await request.json()
    # {'coin_name': 'LINA', 'current_price': 0.011833, 'current_time': '2024-03-01 16:57:42'}
    coin_name = str(json_data["coin_name"])
    current_price = float(json_data["current_price"])
    current_time = datetime.strptime(str(json_data["current_time"]), "%Y-%m-%d %H:%M:%S")
    token_found_id = getIndexOfCoin(coin_name)
    if token_found_id == -1:
        token_found = Token(symbol=coin_name)
        session.add(token_found)
        tokens.append(token_found)
        print(f"Added new coin: {coin_name}, current price: {current_time} at {current_time}")
    else:
        token_found = tokens[token_found_id]
    token_found.addPriceEntry(current_price, current_time)

    return {"response": "ok"}


def migrateJSONtoDB():
    if not os.path.exists("prices.json"):
        file = open("prices.json", 'w')
        file.write("[]")
        file.close()
    _tokens: [] = json.loads(open("prices.json", "r").read())
    for token_from_file in _tokens:
        __token = Token(symbol=token_from_file["symbol"])
        __token.currency = token_from_file["currency"]
        for price_history_entry in token_from_file["price_history"]:
            try:
                timestamp = price_history_entry["datetime"]
            except:
                timestamp = price_history_entry["timestamp"]
            __token.token_prices.append(TokenPrice(price=price_history_entry["price"], datetime=timestamp))
        session.add(__token)
        session.commit()


if __name__ == "__main__":
    if not os.path.exists("database.db"):
        # Migrate from json
        engine = create_engine("sqlite:///database.db")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()

        print("Starting to migrate from JSON to SQLite")
        time_start = datetime.now()
        migrateJSONtoDB()
        time_end = datetime.now()
        print(f"Migrating completed... Took {time_end - time_start}")
    else:
        engine = create_engine("sqlite:///database.db")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()

    tokens: List[Token] = session.query(Token).all()

    manager = multiprocessing.Manager()
    endpoints = manager.list()
    fetcher_process = Process(target=setup_endpoints, args=(endpoints,))
    fetcher_process.start()

    uvicorn.run(app, host="0.0.0.0", port=PORT_TO_RUN_UVICORN, log_level="error")
