import requests


class Endpoint:
    def __init__(self):
        self.protocol: str = "http"
        self.port: int = 80
        self.url = ""

    def getTokens(self):
        resp = requests.get(f"{self.protocol}://{self.url}:{self.port}/getTokens")
        return resp.json()

    def addToken(self, token_symbol):
        resp = requests.put(f"{self.protocol}://{self.url}:{self.port}/putToken/{token_symbol}")
        return resp.json()

    def removeToken(self, token_symbol):
        resp = requests.delete(f"{self.protocol}://{self.url}:{self.port}/deleteToken/{token_symbol}")
        return resp.json()
