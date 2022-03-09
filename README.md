# Cassandra Access Control by Intezer
We’re releasing an open-source tool you can use now, which we developed as a homemade Just-In-Time database access control tool for our sensitive database.
This tool syncs with our directory service (Jumpcloud), slack, SIEM, and finally, our Apache Cassandra database.

# Prerequisits
1. Create new key space (e.g - ttl_accounts) in your DB to hold jit_accounts table for the ttl feature.
2. Create a new table (jit_accounts) in ttl_accounts key space
`CREATE TABLE intezeraccounts(username text PRIMARY KEY , expirytimestamp timestamp, ttl int, permission text);`

4. table name at cassandraJitLayer.py
5. ip & username at config.yaml
6. region_name = "<your region>" at getTokens.py
7. jumpcloud_creds = get_secret("jc_credentials") at jumpcloud.py
8. JUMPCLOUD_USERGROUP_URI = 'https://console.jumpcloud.com/api/v2/usergroups/<groupnumber>/members' at jumpcloud.py
9. cassandra_jit_rest_api = get_secret('cassandraJitApi') at main.py
10. app.run(ssl_context=('/etc/ssl/file.crt', '/etc/ssl/file.key')) at main.py
