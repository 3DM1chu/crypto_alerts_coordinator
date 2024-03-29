import os
from datetime import datetime, timedelta
from typing import Set
import orjson as json
import requests
from decouple import config
from sqlalchemy import Column, Integer, ForeignKey, Float, String, create_engine
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship, sessionmaker


def getPriceLevels(token_to_find: str):
    price_levels = json.loads(open("price_levels.json", "r").read())
    for token in price_levels:
        token_price_levels = [float(token_price_level) for token_price_level in price_levels[token]]
        if token == token_to_find:
            return token_price_levels
    return []


def checkIfPriceIsAroundPriceLevel(token_to_find: str, current_price: float, max_change: float = 0.01):
    # max_change = 1 -> 100%
    price_levels = getPriceLevels(token_to_find)
    if len(price_levels) > 0:
        for price_level in price_levels:
            if price_level * float(1 - max_change) < current_price < price_level * float(1 + max_change):
                print(price_level)
                return {
                    "result": True,
                    "price_level": price_level
                }
    return {
        "result": False,
        "price_level": 0.0
    }


MINIMUM_PRICE_CHANGE_TO_ALERT_5M = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_5M"))
MINIMUM_PRICE_CHANGE_TO_ALERT_15M = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_15M"))
MINIMUM_PRICE_CHANGE_TO_ALERT_30M = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_30M"))
MINIMUM_PRICE_CHANGE_TO_ALERT_1H = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_1H"))
MINIMUM_PRICE_CHANGE_TO_ALERT_4H = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_4H"))
MINIMUM_PRICE_CHANGE_TO_ALERT_8H = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_8H"))
MINIMUM_PRICE_CHANGE_TO_ALERT_24H = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_24H"))
MINIMUM_PRICE_CHANGE_TO_ALERT_7D = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_7D"))
MINIMUM_PRICE_CHANGE_TO_ALERT_30D = float(config("MINIMUM_PRICE_CHANGE_TO_ALERT_30D"))

TELEGRAM_TOKEN = str(config("TELEGRAM_TOKEN"))
TELEGRAM_CHAT_ID = str(config("TELEGRAM_CHAT_ID"))

Base = declarative_base()

"""
{
 "notification_text": "bla bla bla",
 "notification_type": "price_change",
 "extra":{
  "ratio_if_higher_price": 3.0,
  "went_up": False
 }
}

extra can be empty
types: [price_change, price_level]
"""


def sendNotification(notification_dict: {}):
    notification_text, notification_type, extra = notification_dict.values()
    if notification_type == "price_change":
        if extra["went_up"]:
            format_to_add = "fix\n"
        else:
            format_to_add = "\n"
        ratio_if_higher_price = float(extra["ratio_if_higher_price"])

        # DISCORD
        url = ("https://discord.com/api/webhooks/1214234724902502482/"
               "Mxz0D4ah2vplk_2_RmbnROkDeR5fcwArjE8Y6iERFoAD8YftfwgQtaoBl6M_CIgctRfI")
        requests.post(url, data={"content": f"```{format_to_add}{notification_text}```"})
        if 2.0 <= ratio_if_higher_price < 3:
            url = ("https://discord.com/api/webhooks/1214260685245251667/"
                   "e1DgPPFPdTF8kAPZwrw6Tpwslv0ATLLl8UZTIhBoFgquj5AeyoFXtzsPwZIIimSvKmiY")
            requests.post(url, data={"content": f"```{format_to_add}{notification_text}```"})
        elif ratio_if_higher_price >= 3:
            url = ("https://discord.com/api/webhooks/1214262555338604584/"
                   "dDW94T66wgX9FMZb9eGo-ZEdLptoaSukFTQWoOJc1edkaowcGHk1SukElO1uFNL0wXMf")
            requests.post(url, data={"content": f"```{format_to_add}{notification_text}```"})

    elif notification_type == "price_level":
        url = ("https://discord.com/api/webhooks/1217248564540084314/"
               "8qt6adXJzUtew5K_Et0pGoQ87JLiBE0pWLgEjce5dJGlv4KYagNROJUmSOLuPntbc-Dj")
        requests.post(url, data={"content": f"```fix\n{notification_text}```"})
    else:
        print(f"Dont know type: {notification_type}")
        return


def deprecated_sendTelegramNotification(notification: str, ratio_if_higher_price=0.0, went_up=True):
    if went_up:
        format_to_add = "fix\n"
    else:
        format_to_add = "\n"

    # DISCORD
    url = ("https://discord.com/api/webhooks/1214234724902502482/"
           "Mxz0D4ah2vplk_2_RmbnROkDeR5fcwArjE8Y6iERFoAD8YftfwgQtaoBl6M_CIgctRfI")
    requests.post(url, data={"content": f"```{format_to_add}{notification}```"})
    if 2.0 <= ratio_if_higher_price < 3:
        url = ("https://discord.com/api/webhooks/1214260685245251667/"
               "e1DgPPFPdTF8kAPZwrw6Tpwslv0ATLLl8UZTIhBoFgquj5AeyoFXtzsPwZIIimSvKmiY")
        requests.post(url, data={"content": f"```{format_to_add}{notification}```"})
    elif ratio_if_higher_price >= 3:
        url = ("https://discord.com/api/webhooks/1214262555338604584/"
               "dDW94T66wgX9FMZb9eGo-ZEdLptoaSukFTQWoOJc1edkaowcGHk1SukElO1uFNL0wXMf")
        requests.post(url, data={"content": f"```{format_to_add}{notification}```"})

    # TELEGRAM
    _notification = f"======================\n" + notification
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={notification}"
    requests.get(url).json()


class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True)


class TokenPrice(BaseModel):
    __tablename__ = "token_prices"

    token_id: Mapped[int] = mapped_column(Integer, ForeignKey("tokens.id"))
    # token: Mapped[Token] = relationship(back_populates="token_prices")
    price = Column(Float)
    datetime = Column(String)

    def getDateTime(self):
        return datetime.strptime(str(self.datetime), "%Y-%m-%d %H:%M:%S")


class Token(BaseModel):
    __tablename__ = "tokens"

    symbol = Column(String)
    currency = Column(String, default="USD")
    token_prices: Mapped[Set[TokenPrice]] = relationship()

    def getCurrentPrice(self):
        if not self.token_prices:
            return 0.0

        last = self.getNearestPriceEntryToTimeframe(time_frame={"minutes": 1})
        # print(last.price)
        return last.price if last is not None else 0.0

    def addPriceEntry(self, price: float, _datetime: datetime, session):
        if self.getCurrentPrice() == price:
            return
        new_token_price = TokenPrice(price=price, datetime=_datetime)
        self.token_prices.add(new_token_price)
        session.add(new_token_price)
        session.commit()
        self.checkIfPriceChanged(time_frame={"minutes": 5},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_5M,
                                 _current_price=price, _current_datetime=_datetime)
        self.checkIfPriceChanged(time_frame={"minutes": 15},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_15M,
                                 _current_price=price, _current_datetime=_datetime)
        self.checkIfPriceChanged(time_frame={"minutes": 30},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_30M,
                                 _current_price=price, _current_datetime=_datetime)
        self.checkIfPriceChanged(time_frame={"hours": 1},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_1H,
                                 _current_price=price, _current_datetime=_datetime)
        self.checkIfPriceChanged(time_frame={"hours": 4},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_4H,
                                 _current_price=price, _current_datetime=_datetime)
        self.checkIfPriceChanged(time_frame={"hours": 8},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_8H,
                                 _current_price=price, _current_datetime=_datetime)
        self.checkIfPriceChanged(time_frame={"hours": 24},
                                 min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_24H,
                                 _current_price=price, _current_datetime=_datetime)
        # self.checkIfPriceChanged(time_frame={"days": 7},
        #                         min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_7D,
        #                         _current_price=price, _current_datetime=_datetime)
        # self.checkIfPriceChanged(time_frame={"days": 30},
        #                         min_price_change_percent=MINIMUM_PRICE_CHANGE_TO_ALERT_30D,
        #                         _current_price=price, _current_datetime=_datetime)

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
            time_difference = abs(entry.getDateTime() - reference_time)

            # Check if the current entry is closer than the current closest entry
            if time_difference < closest_difference:
                closest_entry = entry
                closest_difference = time_difference

        return closest_entry

    def checkIfPriceChanged(self, time_frame, min_price_change_percent: float, _current_price, _current_datetime):
        # print(f"{self.getCurrentPrice()} | {len(self.price_history)}")
        historic_price_obj = self.getNearestPriceEntryToTimeframe(time_frame)
        historic_price = historic_price_obj.price
        historic_price_timestamp = (datetime.strptime(historic_price_obj.datetime, '%Y-%m-%d %H:%M:%S')
                                    + timedelta(hours=1))

        ATH_ATL = self.checkIfPriceWasATHorATL(time_frame, _current_price)
        wasATH = ATH_ATL["wasATH"]
        wasATL = ATH_ATL["wasATL"]
        if _current_price > historic_price and wasATH:
            price_change = (_current_price / historic_price * 100) - 100
            price_change = float("{:.3f}".format(price_change))
            notification = (f"{self.symbol}\n"
                            f"{historic_price} => {_current_price}$\n"
                            f"ATH in {time_frame}\n"
                            f"📗{price_change}%\n"
                            f"{historic_price_timestamp} | {_current_datetime}")
            if price_change >= min_price_change_percent:
                notification_to_send = {
                    "notification_text": notification,
                    "notification_type": "price_change",
                    "extra": {
                        "ratio_if_higher_price": float(price_change / min_price_change_percent),
                        "went_up": True
                    }
                }
                sendNotification(notification_to_send)

        elif _current_price < historic_price and wasATL:
            price_change = 100 - (_current_price / historic_price * 100)
            price_change = float("{:.3f}".format(price_change))
            notification = (f"{self.symbol}\n"
                            f"{historic_price} => {_current_price}$\n"
                            f"ATL in {time_frame}\n"
                            f"📉{price_change}%\n"
                            f"{historic_price_timestamp} | {_current_datetime}\n")
            if price_change >= min_price_change_percent:
                notification_to_send = {
                    "notification_text": notification,
                    "notification_type": "price_change",
                    "extra": {
                        "ratio_if_higher_price": float(price_change / min_price_change_percent),
                        "went_up": False
                    }
                }
                sendNotification(notification_to_send)
        else:
            price_change = 100 - (_current_price / historic_price * 100)
            price_change = float("{:.3f}".format(price_change))
            notification = (f"{self.symbol}\n"
                            f"📉{price_change}%\n"
                            f"{historic_price} => {_current_price}$\n"
                            f"{historic_price_timestamp} | {_current_datetime}\n"
                            f"======================")
            if price_change >= min_price_change_percent:
                print(notification)

        # PRICE LEVEL CHECKS
        result_is_true, price_level = checkIfPriceIsAroundPriceLevel(str(self.symbol), _current_price, 0.015).values()
        if result_is_true:
            notification = (f"{self.symbol}\n"
                            f"is near price level {price_level}$\n"
                            f"Current price: {_current_price}$\n"
                            f"{_current_datetime}")
            notification_to_send = {
                "notification_text": notification,
                "notification_type": "price_level",
                "extra": {}
            }
            sendNotification(notification_to_send)

    def checkIfPriceWasATHorATL(self, time_delta, _current_price):
        # Define the time threshold (1 hour)
        time_threshold = timedelta(**time_delta)

        result = {
            "wasATH": True,
            "wasATL": True
        }

        # Iterate over price history
        for entry in self.token_prices:
            # Check if the timestamp is within the time threshold
            if datetime.now() - entry.getDateTime() < time_threshold:
                # Check if the price has changed
                if entry.price > _current_price:
                    result["wasATH"] = False
                elif entry.price < _current_price:
                    result["wasATL"] = False
        return result


class Repository:
    def __init__(self):
        self.session = None
        self.tokens: Set[Token] = set()

    def addNewToken(self, symbol: str):
        newToken = Token(symbol=symbol)
        self.session.add(newToken)
        self.tokens.add(newToken)
        self.session.commit()
        return newToken

    def findToken(self, symbol: str):
        _id: int = 0
        for entry in self.tokens:
            if entry.symbol == symbol:
                return entry, _id
            _id += 1
        return None, -1

    def initializeDB(self):
        if not os.path.exists("database.db"):
            # Migrate from json
            engine = create_engine("sqlite:///database.db")
            Base.metadata.create_all(engine)
            self.session = sessionmaker(bind=engine)()

            print("Starting to migrate from JSON to SQLite")
            time_start = datetime.now()
            self.migrateJSONtoDB()
            time_end = datetime.now()
            print(f"Migration completed... Took {time_end - time_start}")
        else:
            engine = create_engine("sqlite:///database.db")
            Base.metadata.create_all(engine)
            self.session = sessionmaker(bind=engine)()

        self.tokens = set(self.session.query(Token).all())
        print(f"Loaded {len(self.tokens)} tokens")

    def migrateJSONtoDB(self):
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
                __token.token_prices.add(TokenPrice(price=price_history_entry["price"], datetime=timestamp))
            self.session.add(__token)
            self.session.commit()
