from sqlsoup import SQLSoup
import datetime
import json
import time
import market
import os


script_path = os.path.dirname(os.path.realpath(__file__))
config = json.load(open(script_path+"/config.json", 'r'))

DB = SQLSoup("mysql://{}:{}@{}:{}/{}".format(config['db_user'], 
    config['db_pass'], config['db_host'], config['db_port'], config['db_name']))


def main():
    next_account = DB.apk_accounts.filter("""
        auth_token = ''
        AND
        disabled = 0
        AND
        (TIMEDIFF(NOW(), last_login) > TIME('00:01:00') OR last_login= 0)
    """).order_by("last_used ASC").first()

    if not next_account:
        print("No account ready to login")
        return

    next_account.last_login = datetime.datetime.now()
    DB.commit()

    try:
        m = market.Market()
        token = m.login(next_account.username, next_account.password, 
                next_account.android_id)
        next_account.auth_token = token
        next_account.logins += 1
        DB.commit()
        print("{} login successful.".format(next_account.username))
    except market.LoginException as e:
        next_account.disabled = True
        DB.commit()
        print("{} login failed.".format(next_account.username))
        print(e)


if __name__ == '__main__':
    main()
