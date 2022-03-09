from jumpcloud import get_data_from_jumpcloud
from cassandraBrokerLayer import cassandra_users_broker
import logging.config
from ttling import ttl_management

logFileName = '/var/log/cassandra_access_control.log'
logger = logging.getLogger('cassandra-broker')
logging.config.dictConfig({
    'version': 1,'disable_existing_loggers': False,
    'formatters': {'default': {'format': '%(asctime)s %(levelname)s %(name)s %(message)s'},},
    'handlers': {'file':{'class':'logging.handlers.RotatingFileHandler',
            'maxBytes':50000,
            'backupCount':5,
            'level':'INFO',
            'formatter': 'default',
            'filename': logFileName,
            'mode':'a'},},
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
})

if __name__ == '__main__':
    logger.info('Started Broker app')
    # Fetch users from jumpcloud user group to make sure users are provisioned in db
    intezer_user_emails = get_data_from_jumpcloud()
    cassandra_users_broker(intezer_user_emails)
    ttl_management()

    logger.info('Finised running Broker app!')
