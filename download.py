from sqlsoup import SQLSoup
import json
import time
import market

config = json.load(open("config.json", 'r'))

DB = SQLSoup("mysql://{}:{}@{}:{}/{}".format(config['username'], 
    config['password'], config['host'], config['port'], config['database']))


def fetch_app(app, account):
    m = market.Market(account.auth_token, account.android_id)
    app_info = m.get_app_info(app.package)
    m.download(app_info, "{}/{}.apk".format(config['apk_path'], app.package))
    return app_info

def main():
    print("APK Downloader started")
    while True:
        next_app = DB.apk_apps.filter("""
            last_fetched = 0
            OR
            TIMEDIFF(NOW(), last_fetched) > TIME('12:00:00')
        """).order_by("last_fetched ASC").first()

        if not next_app:
            print("No apps ready for download")
            time.sleep(1)
            continue

        print next_app

        next_account = DB.apk_accounts.filter("""
            (TIMEDIFF(NOW(), last_used) > TIME('00:01:00') OR last_used = 0)
            AND
            auth_token != ''
        """).order_by("last_used ASC").first()

        if not next_account:
            print("No accounts available")
            time.sleep(1)
            continue

        # Update account/app records to mark as used
        next_app.last_fetched = datetime.datetime.now()
        next_account.last_used = datetime.datetime.now()
        DB.commit()

        # Retrieve actual app data 
        app_info = fetch_app(next_app, next_account)

        # Update records with retrieved app info
        next_app.title = app_info['title']
        next_app.author = app_info['author']
        next_app.ratings_count = app_info['ratings_count']
        next_app.last_version = app_info['version']
        if not next_app.initial_version:
            next_app.initial_version = app_info['version']
        next_account.downloads += 1
        DB.commit()


if __name__ == '__main__':
    main()
