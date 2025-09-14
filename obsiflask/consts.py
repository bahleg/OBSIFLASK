"""
Some basic app constants, shared across modules
"""
import re

APP_NAME = 'OBSIFLASK'
"""
APP Name for flask
"""
COVER_KEY = 'cover'
"""
Cover key for bases in a card view
"""
MAX_FILE_SIZE_MARKDOWN = 1024 * 1024
"""
Currently files with large size will be ignored during file properties analyzis, graph building
"""

wikilink = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
"""
Regex for wikilink 
"""
hashtag = re.compile('#[\w\-]+')
"""
Rege for hashtag
"""
