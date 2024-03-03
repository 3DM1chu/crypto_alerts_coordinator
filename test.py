from datetime import datetime
from time import sleep

import requests


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
        file.write(file_content)

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
        file.write(file_content)
    return len(resp.text.split())
