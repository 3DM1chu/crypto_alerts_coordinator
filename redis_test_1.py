from datetime import datetime
from time import sleep
import orjson as json

import requests

import main_sql_sets


def count_words_at_url(url):
    resp = requests.get(url)

    # Convert datetime object to string
    bro_datetime_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Using underscores and dashes for file name

    # Define the file name
    file_name = f"{bro_datetime_str}.txt"

    # Define the content of the file
    file_content = "This is a sample file content."

    # Write content to the file
    with open(file_name, 'w') as file:
        file.write(str(json.dumps(main_sql_sets.tokens)))

    sleep(15)
    print(len(resp.text.split()))


    # Convert datetime object to string
    bro_datetime_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Using underscores and dashes for file name

    # Define the file name
    file_name = f"{bro_datetime_str}.txt"

    # Define the content of the file
    file_content = "This is a sample file content."

    # Write content to the file
    with open(file_name, 'w') as file:
        file.write(str(json.dumps(main_sql_sets.tokens)))
    return len(resp.text.split())
