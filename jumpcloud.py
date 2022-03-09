import requests, json
from getTokens import get_secret
import logging

JUMPCLOUD_USERGROUP_URI = 'https://console.jumpcloud.com/api/v2/usergroups/<groupnumber>/members'
logger = logging.getLogger('cassandra-broker')


def get_data_from_jumpcloud():

    jumpcloud_user_ids_collection = []
    jumpcloud_user_emails_collection = []

    jumpcloud_creds = get_secret("jc_credentials")
    result = json.loads(jc_credentials)
    jumpcloudApi = result['jumpcloudApi']

    logger.info('Querying secrets - success')
    logger.info('Invoke jumpcloud user group API')

    s = requests.session()
    s.headers = {'x-api-key': jumpcloudApi}

    try:
        r = s.get(JUMPCLOUD_USERGROUP_URI)
    except Exception:
        logger.exception('Error while invoking jumpcloud API - usergroups endpoint')

    else:
        if r.status_code != 200:
            e = r.json()
            logger.error(e['error'])
        else:
            json_response = json.loads(r.text)
            for user in json_response:
                userid = user['to']['id']
                jumpcloud_user_ids_collection.append(userid)
    try:
        for user in jumpcloud_user_ids_collection:
            r = s.get(f'https://console.jumpcloud.com/api/systemusers/{user}')
            if r.status_code != 200:
                e = r.json()
                logger.error(e['error'])
            else:
                jumpcloud_user_emails_collection.append(json.loads(r.text)['email'])

        return jumpcloud_user_emails_collection

    except Exception:
        logger.exception('Error while invoking jumpcloud API - systemusers endpoint')
