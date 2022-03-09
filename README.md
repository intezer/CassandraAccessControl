# Cassandra Access Control by Intezer Security (security@intezer.com)
We’re releasing an open-source tool you can use now, which we developed as a homemade Just-In-Time database access control tool for our sensitive database.
This tool syncs with our directory service (Jumpcloud), slack, SIEM, and finally, our Apache Cassandra database.

# Prerequisits
1. Create new key space (e.g - ttl_accounts) in your DB to host jit_accounts table for the ttl feature.
2. Create a new table (jit_accounts) in ttl_accounts key space
`CREATE TABLE intezeraccounts(username text PRIMARY KEY , expirytimestamp timestamp, ttl int, permission text);`
3. It is recommended to create a dedicated service user to interacte with DB
`CREATE ROLE 'headless_security' WITH SUPERUSER = true AND LOGIN = true AND PASSWORD = '<>'`

4. Update ip & username in config.yaml
5. This service fetch credentials from aws secrets. If you plan to use the same, make sure to update region_name = "<your region>" at getTokens.py
6. Assign secret name in jumpcloud.py: `jumpcloud_creds = get_secret("jc_credentials")`
7. If using jumpcloud, assign `groupnumber` in jumpcloud.py: `JUMPCLOUD_USERGROUP_URI = 'https://console.jumpcloud.com/api/v2/usergroups/<groupnumber>/members'z`
8. Assign secret name in main.py: `cassandra_jit_rest_api = get_secret('cassandraJitApi')`
9. Generate SSL and assign its location in main.py: `app.run(ssl_context=('/etc/ssl/file.crt', '/etc/ssl/file.key'))`
