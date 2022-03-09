import secrets
import datetime

def generate_random_secret():

    return secrets.token_urlsafe(18)

def get_hours_diff(expirytimestamp, ttl):
    nowtimestamp = datetime.datetime.utcnow()
    diff = expirytimestamp - nowtimestamp
    hoursdiff = diff.seconds / 3600
    expire = ttl - hoursdiff

    if expire >= ttl:
        # TTL expired
        return False
    if expire < 0:
        # TTL expired
        return False
    else:
        # TTL not expired
        return True
