import asyncio
import orjson as json
import multiprocessing
from datetime import datetime
from multiprocessing import Process
import redis
import requests
import uvicorn
from decouple import config
from fastapi import FastAPI, Request
from models import Repository
from redis_test_1 import count_words_at_url
from redis import Redis
from rq import Queue


PORT_TO_RUN_UVICORN = int(config("PORT_TO_RUN_UVICORN"))


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


def setup_endpoints(_endpoints: list):
    coins_to_check = json.loads(open("coins.json", "r").read())
    _endpoints.append({"url": "http://frog01.mikr.us:21591/putToken/", "tokens":
                      [coin_from_file["symbol"] for coin_from_file in coins_to_check]})
    asyncio.run(startPollingEndpoints(_endpoints))


app = FastAPI()


@app.post("/addTokenPrice")
async def addTokenToCheck(request: Request):
    json_data = await request.json()
    # {'coin_name': 'LINA', 'current_price': 0.011833, 'current_time': '2024-03-01 16:57:42'}
    symbol = str(json_data["symbol"])
    current_price = float(json_data["current_price"])
    current_time = datetime.strptime(str(json_data["current_time"]), "%Y-%m-%d %H:%M:%S")
    token_found, _ = repo.findToken(symbol)
    if token_found is None:
        token_found = repo.addNewToken(symbol)
        print(f"Added new token: {symbol}, current price: {current_time} at {current_time}")
    token_found.addPriceEntry(current_price, current_time, repo.session)
    return {"response": "ok"}


if __name__ == "__main__":
    repo = Repository()
    repo.initializeDB()
    conn = redis.from_url("redis://localhost:6379")

    q = Queue(connection=Redis())
    q.enqueue(count_words_at_url, args=('http://nvie.com', repo.tokens, set("ee")))

    manager = multiprocessing.Manager()
    endpoints = manager.list()
    fetcher_process = Process(target=setup_endpoints, args=(endpoints,))
    fetcher_process.start()

    uvicorn.run(app, host="0.0.0.0", port=PORT_TO_RUN_UVICORN, log_level="error")
