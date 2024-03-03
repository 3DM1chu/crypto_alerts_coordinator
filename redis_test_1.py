from datetime import datetime
from time import sleep
import orjson as json


def count_words_at_url(url, tokens):
    bro_datetime_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Using underscores and dashes for file name
    file_name = f"{bro_datetime_str}.txt"

    with open(file_name, 'w') as file:
        file.write(str(json.dumps(tokens)))

    sleep(15)

    bro_datetime_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Using underscores and dashes for file name
    file_name = f"{bro_datetime_str}.txt"

    with open(file_name, 'w') as file:
        file.write(str(json.dumps(tokens)))

    return url
