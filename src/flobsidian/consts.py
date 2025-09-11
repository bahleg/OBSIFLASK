import re

APP_NAME = 'flobsidian'

COVER_KEY = 'cover'
INDEX_UPDATE_TIME = 5 * 60
MESSAGE_LIST_SIZE = 100
MAX_FILE_SIZE_MARKDOWN = 1024*1024 # 1 MB
MaxViewErrors = 50
SEARCH_PREVIEW_CHARS = 100

wikilink = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
hashtag = re.compile('#[\w\-]+')