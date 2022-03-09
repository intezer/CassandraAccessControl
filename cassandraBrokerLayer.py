import logging
from cassandra.cluster import Session
from connectToCassandra import connect_to_cassandra
from utils import generate_random_secret

logger = logging.getLogger('cassandra-broker')
session: Session = None


def create_role_for_user(user, session):
    secret = generate_random_secret()
    try:
        session.execute('CREATE ROLE %s WITH PASSWORD = %s and login = true', (user, secret))
        logger.info(f'User {user} created successfully in DB')

    except Exception:
        logger.exception(f'Error while creating role for user {user} in db')
        return

#This function querying roles table and comparing the users found in the table with the
#users from Jumpcloud group. if user was not found in DB roles table but found in Jumpcloud,
#create_role_for_user function above will create it with a random password.
def cassandra_users_broker(intezer_emails_from_jumpCloud):

    global session
    session = connect_to_cassandra()
    for email in intezer_emails_from_jumpCloud:
        user = email.split("@")[0]

        # Checking if user exists in DB
        logger.info(f'Checking if user {user} exists in DB')
        query = session.prepare('select role FROM system_auth.roles where role=?')
        roles = []
        roles.append(user)
        for username in roles:
            try:
                row = session.execute(query, [username]).one()
            except Exception:
                logger.exception('Exception on querying system_auth.roles table')
                return

            if row:
                logger.info(f'User {user} already in DB. Skipping')
                #Append user to DB

            else:
                logger.info(f'User {user} Not in DB. Will create user in roles table')
                create_role_for_user(user, session)
