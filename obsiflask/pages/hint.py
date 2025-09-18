import datetime

from obsiflask.consts import DATE_FORMAT


def get_hint(vault: str, context: str):
    date = datetime.datetime.now().strftime(DATE_FORMAT)
    return [{'text': date, 'short': 'TODAY', 'erase': 0}]
