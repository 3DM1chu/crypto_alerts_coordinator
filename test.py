from time import sleep

import requests


def count_words_at_url(url):
    resp = requests.get(url)
    sleep(15)
    print(len(resp.text.split()))
    return len(resp.text.split())
