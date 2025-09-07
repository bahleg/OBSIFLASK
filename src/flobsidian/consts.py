import re

APP_NAME = 'flobsidian'

COVER_KEY = 'cover'
INDEX_UPDATE_TIME = 5 * 60
MESSAGE_LIST_SIZE = 100
MaxViewErrors = 50

wikilink = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
hashtag = re.compile('#[\w\-]+')