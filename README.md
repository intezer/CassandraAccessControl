# Cassandra Access Control by Intezer Security (security@intezer.com)
We’re releasing an open-source tool you can use now, which we developed as a homemade Just-In-Time database access control tool for our sensitive database.
This tool syncs with our directory service (Jumpcloud), slack, SIEM, and finally, our Apache Cassandra database.

# Prerequisits
1. Create new key space (e.g - ttl_accounts) in your DB to host jit_accounts table for the ttl feature.
2. Create a new table (jit_accounts) in ttl_accounts key space
`CREATE TABLE intezeraccounts(username text PRIMARY KEY , expirytimestamp timestamp, ttl int, permission text);`
3. It's recommended to create a dedicated service user to interacte with DB
`CREATE ROLE '<some_app_user>' WITH SUPERUSER = true AND LOGIN = true AND PASSWORD = '<>'`

4. Assign IP & Username in config.yaml
5. This service fetch credentials from AWS secrets. If you plan to use the same method, make sure to update `region_name = "<your region>"` in getTokens.py
6. Assign AWS secret name in jumpcloud.py: `jumpcloud_creds = get_secret("jc_credentials")`
7. If using jumpcloud, assign `groupnumber` in jumpcloud.py: `JUMPCLOUD_USERGROUP_URI = 'https://console.jumpcloud.com/api/v2/usergroups/<groupnumber>/members'z`
8. Assign AWS secret name in main.py: `cassandra_jit_rest_api = get_secret('cassandraJitApi')`
9. Generate SSL and assign its location in main.py: `app.run(ssl_context=('/etc/ssl/file.crt', '/etc/ssl/file.key'))`

# Service components:
Jit-Service is a REST API web service with five main capabilities:
Accepts (with validation & authentication) HTTP(s) requests from slack.
Invoke jumpcloud API for user validation.
Invoke Cassandra for role settings and password\token management
Returns HTTP response with a one-time token to access the database.
Logging.
TTLING Service:
Invoke jumpcloud API for user validation and provisioning.
Revokes expired one-time tokens.

Both services are running in Kubernetes environment.
