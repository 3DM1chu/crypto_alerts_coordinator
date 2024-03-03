from time import sleep


def count_words_at_url(url: str, tokens: set, tokens2: set):
    print(f"BEFORE 15s - {len(tokens)}")
    sleep(15)
    print(f"AFTER 15s - {len(tokens)}")

    return url
