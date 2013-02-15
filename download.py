import json
import datetime
import logging
import time
import os
import sys

from sqlsoup import SQLSoup
from boto.s3.key import Key
import boto
import pytz

import market


class AlreadyFetchedException(Exception): pass


config = json.load(open("config.json", 'r'))
logging.basicConfig(filename='downloader.log', level=logging.DEBUG)
logging.getLogger('boto').setLevel(logging.CRITICAL)

S3 = boto.connect_s3(config['s3_access_key'], 
        config['s3_access_secret'])
S3_Bucket = S3.get_bucket("wrw_apks")
DB = SQLSoup("mysql://{}:{}@{}:{}/{}?charset=utf8&use_unicode=0".format(
    config['username'], config['password'], config['host'], config['port'], 
    config['database']))


def fetch_app(app, account):
    logging.debug("Getting app info for {}".format(app.package))
    m = market.Market(account.auth_token, account.android_id)
    app_info = m.get_app_info(app.package)

    if app.last_version >= int(app_info['version']):
        # Don't bother downloading if the version hasn't changed
        logging.debug("App {} already up to date, skip download".format(
            app.package))
        return app_info

    file_name = "{}/{}.apk".format(config['apk_path'], app.package)
    m.download(app_info, file_name)
    logging.debug("Downloaded {} to {}".format(app.package, file_name))

    s3_key = Key(S3_Bucket)
    s3_key.key = file_name
    s3_key.set_contents_from_filename(file_name)
    s3_key.make_public()
    logging.debug("Put {} to S3".format(file_name))

    os.remove(file_name)
    logging.debug("Removing local file {}".format(file_name))

    return app_info


def main():
    logging.info("APK Downloader started")

    if not os.path.exists("./{}".format(config['apk_path'])):
        logging.info("Creating download path for APKs: {}".format(
            config['apk_path']))
        os.makedirs("./{}".format(config['apk_path']))
    else:
        logging.info("Path for APKs already exists: {}".format(
            config['apk_path']))

    while True:
        logging.debug("Fetching next app...")
        next_app = DB.apk_apps.filter("""
            last_fetched = 0
            OR
            TIMEDIFF(NOW(), last_fetched) > TIME('12:00:00')
        """).order_by("last_fetched ASC").first()

        if not next_app:
            time.sleep(1)
            continue

        logging.debug("Fetching next account...")
        next_account = DB.apk_accounts.filter("""
            (TIMEDIFF(NOW(), last_used) > TIME('00:00:10') OR last_used = 0)
            AND
            auth_token != ''
        """).order_by("last_used ASC").first()

        if not next_account:
            time.sleep(1)
            continue

        logging.debug("-"*20)
        logging.debug("Using {} to retrieve {}".format(next_account.username,
            next_app.package))

        # Update account/app records to mark as used
        next_app.last_fetched = datetime.datetime.now(tz=pytz.timezone("US/Eastern"))
        next_account.last_used = datetime.datetime.now(tz=pytz.timezone("US/Eastern"))
        DB.commit()

        logging.debug("Took app and account out of queue for processing")

        # Retrieve actual app data 
        try:
            app_info = fetch_app(next_app, next_account)
            # Update records with retrieved app info
            next_app.title = app_info['name']
            next_app.author = app_info['creator']
            next_app.ratings_count = app_info['ratings_count']
            next_app.last_version = app_info['version']
            if not next_app.initial_version:
                next_app.initial_version = app_info['version']
            next_account.downloads += 1
            logging.debug("Updating DB info for {}".format(next_app.package))

        except market.NotAuthenticatedException, e:
            # Force this account to login again
            next_account.auth_token = ''
            logging.warn("Request by {} failed, not authenticated".format(
                next_account.username))

        except market.SearchException, e:
            # Mark package as not found
            next_app.not_found = True
            logging.warn("Package {} not found".format(next_app.package))

        except Exception, e:
            logging.critical("App {} raised exception {}".format(
                next_app.package, e))
            logging.critical("Account: {} ({})".format(next_account.username,
                next_account.id))

        try:
            DB.commit()
        except:
            logging.critical("App {} raised exception {}".format(
                next_app.package, e))
            logging.critical("Account: {} ({})".format(next_account.username,
                next_account.id))

            next_app.title = "error"
            next_app.author = "error"
            DB.commit()

        logging.debug("Finished working with {}".format(next_app.package))


if __name__ == '__main__':
    main()
