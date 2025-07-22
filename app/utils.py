import re

def validate_youtube_url(url):
    return bool(re.match(r'^https?://(www\.)?youtube\.com|youtu\.be', url)) 