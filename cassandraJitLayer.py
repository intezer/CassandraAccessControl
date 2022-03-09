
from cassandra.cluster import Session
import logging
import datetime
from connectToCassandra import connect_to_cassandra
from utils import generate_random_secret, get_hours_diff

session: Session = None
logger = logging.getLogger('cassandra-jit')
SELECT_TTL = 9
MODIFY_TTL = 2
ADMIN_TTL = 1

def get_calculated_hours_diff_timestamp(hours_to_append):

    current_date_and_time = datetime.datetime.utcnow()
    hours_added = datetime.timedelta(hours=hours_to_append)
    future_date_and_time = current_date_and_time + hours_added
    return future_date_and_time.strftime('%Y-%m-%dT%H:%M:%S+0000')


def append_to_jit_accounts_table(user, hours_to_append, permissions_to_set):

    expirytimestamp = get_calculated_hours_diff_timestamp(hours_to_append)

    logger.info(f'Inserting user {user} to jit_accounts table with {hours_to_append} hours ttl and {permissions_to_set} permissions')
    try:
        session.execute('INSERT INTO accounts_ttl.jit_accounts(username,expirytimestamp,ttl, permission)VALUES (%s, %s, %s, %s)',
                        (user,expirytimestamp, hours_to_append, permissions_to_set))

        logger.info(f'Successfully inserted user {user} to jit_accounts table with {hours_to_append} hours ttl and {permissions_to_set} permissions')
    except Exception:
        logger.exception(f'Error while Inserting user {user} to jit_accounts table')


def reset_user_password(user):
    secret = generate_random_secret()
    try:
        # RESET USER PASSWORD
        session.execute('ALTER USER %s WITH PASSWORD %s', (user, secret))
        logger.info(f'Successfully reset the user {user} password on DB')
        return secret
    except Exception:
        logger.exception(f'Error while revoke user {user} permissions')
        return

def reset_password_and_grant(user,permissionsToSet):

    logger.info(f'Reset user {user} password and granting permissions')
    secret = reset_user_password(user)

    #REVOKE ALL PERMISSIONS:
    revoke = session.prepare('SELECT username FROM accounts_ttl.jit_accounts where username=?')
    user_to_revoke = []
    user_to_revoke.append(user)
    for user_ in user_to_revoke:
        try:
            session.execute(revoke, [user_]).one()
            logger.info(f'Successfully revoked all permissions from user {user_}')
        except Exception:
            logger.exception(f'Error while revoke user {user_} permissions')
            return

    for permission in permissionsToSet:

        try:
            session.execute(f"GRANT {permission} ON KEYSPACE artifacts TO {user}")
            session.execute(f"GRANT {permission} ON KEYSPACE code_reuse TO {user}")
            session.execute(f"GRANT {permission} ON KEYSPACE api TO {user}")
            session.execute(f"GRANT {permission} ON KEYSPACE accounts TO {user}")
            session.execute(f"GRANT {permission} ON KEYSPACE diagnosis_system TO {user}")

            logger.info(f'Successfully granted {permission} permissions to user {user}')
            return secret

        except Exception:
            logger.exception(f'Error granting permissions for user {user}')
            return



def check_if_user_has_valid_ttl(user, permission_asked_by_user):

    #This function does 2 things:
    # 1. checking if query return results of the inherited user - if it does then user still have valid token
    # 2. checking if the token ttl has not expired (compensated control for cassandraBroker script)
    # 3. checking if the user asked for a different permissions from the previous one.
    # if the permission asked found identical to the permission in the DB, the process returns - Has a valid TTL token. else - continue to 3.

    query = session.prepare('SELECT username,expirytimestamp,ttl,permission FROM accounts_ttl.jit_accounts where username=?')
    jumpcloud_users = []
    jumpcloud_users.append(user)
    for jc_user in jumpcloud_users:
        try:
            rows = session.execute(query,[jc_user]).one()
            logger.info(f'Successfully queried user {user} from jit_accounts table')
        except Exception:
            logger.exception(f'Error while querying user {user} from jit_accounts table')
            return
        if rows:
            # if rows, passed check # 1
            for user in rows:
                is_ttl_valid = get_hours_diff(rows.expirytimestamp,rows.ttl)
                if is_ttl_valid:
                    #check # 3
                    if permission_asked_by_user == rows.permission:
                        logger.info(f'User {user} found in jit_accounts - Has a valid TTL token')
                        return True
                    else:
                        # continue to generate new password and permissions
                        return False
                else:
                    # continue to generate new password and permissions
                    return False
        else:
            # continue to generate new password and permissions
            return False

def cassandra_entry_point(user,permission):

    global session
    session = connect_to_cassandra()
    if session:
        user = user.split("@")[0]

        logger.info(f'Checking if user {user} TTL still valid')

        is_ttl_valid = check_if_user_has_valid_ttl(user, permission)
        if is_ttl_valid:
            logger.info(f'TTL token for user {user} is still valid. Will not continue with process')
            return "validttl"

        logger.info(f'Enrolling {permission} permissions process requested by {user}')
        logger.info(f'Checking if user {user} exists in DB')

        query = session.prepare('SELECT role FROM system_auth.roles where role=?')
        user_list = []
        user_list.append(user)
        for user in user_list:
            try:
                query_result = session.execute(query, [user]).one()
                logger.info(f'Successfully queried user {user} from roles table')
            except Exception:
                logger.exception('Exception on querying system_auth.roles table')
                return

            if query_result:
                for user_row in query_result:
                    if 'SELECT' in permission:
                        permissions_to_set = ['SELECT']
                        result = reset_password_and_grant(user_row,permissions_to_set)
                        append_to_jit_accounts_table(user_row, SELECT_TTL, 'SELECT')
                        if result:
                            return {'onTimeToken': result, 'user': user_row, 'permission': permission}
                        else:
                            return
                    if 'ADMIN' in permission:
                        permissions_to_set = ["ALTER", "AUTHORIZE", "CREATE", "DROP", "MODIFY", "SELECT"]
                        result = reset_password_and_grant(user_row, permissions_to_set)
                        append_to_jit_accounts_table(user_row, ADMIN_TTL, 'ADMIN')
                        if result:
                            return {'onTimeToken': result, 'user': user_row, 'permission': permission}
                        else:
                            return
                    if 'MODIFY' in permission:
                        permissions_to_set = ['MODIFY', 'SELECT']
                        result = reset_password_and_grant(user_row, permissions_to_set)
                        append_to_jit_accounts_table(user_row, MODIFY_TTL , 'MODIFY')
                        if result:
                            return {'onTimeToken': result, 'user': user_row, 'permission': permission}
                        else:
                            return

            else:
                logger.info(f'User {user} was not found in DB')
                return
    else:
        logger.error('Could not connect to database')
        return
