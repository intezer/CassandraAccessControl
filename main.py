from flask import Flask, request,jsonify
from flask_restful import Api
from flask_httpauth import HTTPBasicAuth
from jumpcloud import get_data_from_jumpcloud
from email_validator import validate_email, EmailNotValidError
import logging.config
import logging
from cassandraJitLayer import cassandra_entry_point
from getTokens import get_secret
import json

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()

logFileName = '/var/log/cassandra_access_control.log'
logger = logging.getLogger('cassandra-jit')
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

def validateEmail(email):
    try:
        valid = validate_email(email)
        email = valid.email
        return email
    except EmailNotValidError as e:
        logger.exception(str(e))
        return False

@auth.verify_password
def verify_password(username, password):
    if username and password:
        cassandra_jit_rest_api = get_secret('cassandraJitApi')
        cassandra_jit_rest_api_result = json.loads(cassandra_jit_rest_api)

        if username in cassandra_jit_rest_api_result['user'] and password in cassandra_jit_rest_api_result['password']:
            logger.info('Credentials authorized')
            return 'authorized!'
        logger.error('Unauthorized Access. Username or password incorrect.')  
    logger.error('Invalid credentials input.')
    

@app.route('/ask', methods=['GET'])
@auth.login_required
def ask_for_permissions():
    email = request.args.get('email')
    if email:
        if not validateEmail(email):
            logger.error(f'Invalid email input. Found {email}')
            return jsonify(message=f'Invalid email {email}'), 400
        else:
            logger.info(f'Email input is valid. Found {email}')
    else:
        logger.error(f'Email not found in request')
        return jsonify(message='Email not found in request'), 400


    permission = request.args.get('permission')
    if permission:
        if permission not in ['SELECT','ADMIN','MODIFY']:
            logger.error(f'Invalid permissions input. Found {permission}. Expected SELECT, ADMIN or MODIFY')
            return jsonify(message=f'Invalid permission {permission}'), 400
        else:
            logger.info(f'Permission property is valid. Found {permission}')
    else:
        logger.error(f'Permission property not found in request')
        return jsonify(message='Permission property not found in request'), 400

    env = request.args.get('env')
    if env:
        if env not in ['PROD', 'STAGE']:
            logger.error(f'Invalid env input. Found {env}. Expected PROD or STAGE')
            return jsonify(message=f'Invalid env property {env}'), 400
        else:
            logger.info(f'env property is valid. Found {env}')
    else:
        logger.error(f'env property not found in request')
        return jsonify(message='env property not found in request'), 400

    user_emails = get_data_from_jumpcloud()
    for email_from_jumpcloud in user_emails:
        if email == email_from_jumpcloud:
            onTimeToken = cassandra_entry_point(email_from_jumpcloud, permission)
            if onTimeToken == "validttl":
                return jsonify(message='Previous One Time Token still valid. Please use it.')
            if onTimeToken:
                logger.info(f'Process ended successfully. {permission} permissions has granted to user {email}')
                return jsonify(message=onTimeToken)
            else:
                logger.error(f'Process ended with errors. {permission} permissions has not granted to user {email}')
                return jsonify(message='An Error occured granting onTimeToken'), 401
    else:
        logger.error(f'User {email} was not found')
        return jsonify(message='User not found'), 401

if __name__ == "__main__":

    logger.info('Started JIT app')
    app.run(ssl_context=('/etc/ssl/file.crt', '/etc/ssl/file.key'))
