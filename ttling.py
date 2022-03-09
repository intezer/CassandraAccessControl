import logging
from datetime import datetime
from cassandra.cluster import Session
import datetime
from connectToCassandra import connect_to_cassandra
from utils import generate_random_secret, get_hours_diff

logger = logging.getLogger('cassandra-broker')
session: Session = None

def reset_password_and_remove(user, session):
    secret = generate_random_secret()
    try:
        session.execute('ALTER USER %s WITH PASSWORD %s', (user, secret))
        logger.info(f'Successfully reset the user {user} password on DB')
    except Exception:
        logger.error(f'Error while resetting password for user {user}')
        return
    else:
        delete = session.prepare('DELETE FROM ttl_accounts.jit_accounts WHERE username=?')
        user_to_delete = []
        user_to_delete.append(user)
        for username in user_to_delete:
            try:
                session.execute(delete, [username])
                logger.info(f'Successfully deleted user {user} from DB')
            except Exception:
                logger.exception(f'Error while deleting user {user} from jit_accounts table')
                return


def ttl_management():

    session = connect_to_cassandra()
    logger.info('Enrolling TTLING process')

    try:
        logger.info(f'Querying all users from jit_accounts table')
        usernames = session.execute('select username,expirytimestamp,ttl FROM ttl_accounts.jit_accounts').all()

    except Exception:
        logger.exception('Exception on querying system_auth.roles table')
        return

    if usernames:
        for role in usernames:
            isttlvalid = get_hours_diff(role.expirytimestamp,role.ttl)
            if not isttlvalid:
                logger.info(f'ttl for {role.username} expired. Enrolling reset and remove from database.')
                reset_password_and_remove(role.username, session)
            else:
                logger.info(f'ttl for {role.username} still not expired. Nothing to do. Exiting TTling process')
    else:
        logger.info('jit_accounts table is empty. Nothing to do. Exiting TTling process')
