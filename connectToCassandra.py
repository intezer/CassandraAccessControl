import logging
from getTokens import get_secret
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Session
import sys
import json
import yaml

logger = logging.getLogger('cassandra-broker')
session: Session = None

def connect_to_cassandra():

    try:
        with open('config.yaml') as f:
            data = yaml.load(f, Loader=yaml.BaseLoader)

    except Exception:
        logger.exception('Unable to fetch cassandra ip from config.json file')
        return

    headless_security_stage = get_secret(data['cassandra_user_name'][0])
    res = json.loads(headless_security_stage)
    dbuser = res['user']
    dbpass = res['password']

    auth_provider = PlainTextAuthProvider(username=dbuser, password=dbpass)
    cluster = Cluster([data['cassandra_end_point'][0]], auth_provider=auth_provider)
    try:
        global session
        session = cluster.connect()
        return session

    except Exception:
        logger.exception('Unable connecting to cassandra')
        return
