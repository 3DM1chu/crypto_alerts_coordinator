from time import sleep

import requests


def count_words_at_url(url):
    resp = requests.get(url)
    sleep(15)
    return len(resp.text.split())