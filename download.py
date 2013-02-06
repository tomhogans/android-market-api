from sqlsoup import SQLSoup
import json
import time
import os
import boto
from boto.s3.key import Key
import market


class AlreadyFetchedException(Exception): pass


config = json.load(open("config.json", 'r'))

S3 = boto.connect_s3(config['s3_access_key'], 
        config['s3_access_secret'])
Bucket = S3.get_bucket("wrw_apks")
DB = SQLSoup("mysql://{}:{}@{}:{}/{}".format(config['username'], 
    config['password'], config['host'], config['port'], config['database']))


def fetch_app(app, account):
    m = market.Market(account.auth_token, account.android_id)
    app_info = m.get_app_info(app.package)
    # TODO: compare app.version < app_info['version'], if so skip download
    file_name = "{}/{}.apk".format(config['apk_path'], app.package)
    m.download(app_info, file_name)

    s3_key = Key(S3_Bucket)
    s3_key.key = file_name
    s3_key.set_contents_from_filename(file_name)
    s3_key.make_public()

    os.remove(file_name)

    return app_info

def main():
    print("APK Downloader started")

    if not os.path.exists("./{}".format(config['apk_path'])):
        os.makedirs("./{}".format(config['apk_path']))

    return

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
