import json
import datetime
import logging
import requests
import urllib
import time
import os
import sys

from boto.s3.key import Key
import boto

import market


class AlreadyFetchedException(Exception): pass

script_path = os.path.dirname(os.path.realpath(__file__))
config = json.load(open(script_path+"/config.json", 'r'))
logging.basicConfig(filename=script_path+'/downloader.log', level=logging.DEBUG)
logging.getLogger('boto').setLevel(logging.CRITICAL)
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(
        logging.CRITICAL)

S3 = boto.connect_s3(config['s3_access_key'], 
        config['s3_access_secret'])
S3_Bucket = S3.get_bucket("wrw_apks")


def send_req(params):
    """ Sends request to HTTP endpoint with params as urlencoded params """
    url = "{}?{}".format(config['endpoint'], urllib.urlencode(params))
    resp = requests.get(url, auth=(config['username'], config['password']))
    try:
        data = json.loads(resp.content)
        return data
    except Exception, e:
        return {}


def get_next_work_item():
    """ Requests an APK to fetch and an account to fetch it with """
    return send_req({'next': 'true'})


def fetch_app(app, account):
    logging.debug("Getting app info for {}".format(app['package']))
    m = market.Market(account['auth_token'], account['android_id'])
    app_info = m.get_app_info(app['package'])


    if int(app['last_version']) >= int(app_info['version']):
        # Don't bother downloading if the version hasn't changed
        logging.debug("App {} already up to date, skip download".format(
            app['package']))
        return app_info

    s3_path = "{}/{}.apk".format(config['apk_path'], app['package'])
    file_name = "{}/{}".format(script_path, s3_path)
    m.download(app_info, file_name)
    logging.debug("Downloaded {} to {}".format(app['package'], file_name))

    s3_key = Key(S3_Bucket)
    s3_key.key = s3_path
    s3_key.set_contents_from_filename(file_name)
    s3_key.make_public()
    logging.debug("Put {} to S3".format(s3_path))

    s3_key = S3_Bucket.get_key(s3_path)
    if s3_key:
        logging.debug("S3 Upload Verified: {}".format(s3_path))
    else:
        logging.warn("S3 Upload Failed: {}".format(s3_path))

    os.remove(file_name)
    logging.debug("Removing local file {}".format(file_name))

    notify_url = "{}{}".format(config['notify_url'], app['package'])
    requests.get(notify_url, 
            auth=(config['notify_user'], config['notify_pass']))
    logging.debug("Hitting {}".format(notify_url))

    return app_info


def main():
    logging.info("APK Downloader started")

    if not os.path.exists(script_path+"/{}".format(config['apk_path'])):
        logging.info("Creating download path for APKs: {}".format(
            config['apk_path']))
        os.makedirs(script_path+"/{}".format(config['apk_path']))
    else:
        logging.info("Path for APKs already exists: {}".format(
            config['apk_path']))

    try:
        work_item = get_next_work_item()
        if not work_item:
            return

        next_app = work_item['app']
        next_account = work_item['account']

        logging.debug("-"*20)
        logging.debug("Using {} to retrieve {}".format(
            next_account['username'], next_app['package']))

        app_info = fetch_app(next_app, next_account)
        send_req({
            'update': app_info['package'],
            'title': app_info['name'].encode('ascii', 'ignore'),
            'author': app_info['creator'].encode('ascii', 'ignore'),
            'version': app_info['version'],
            'ratings_count': app_info['ratings_count'],
        })
        logging.debug("Updating DB info for {}".format(next_app['package']))

    except market.NotAuthenticatedException, e:
        # Force this account to login again
        send_req({'loginfailed': next_account['username']})
        logging.warn("Request by {} failed, not authenticated".format(
            next_account['username']))

    except market.SearchException, e:
        # Mark package as not found
        send_req({'notfound': next_app['package']})
        logging.warn("Package {} not found".format(next_app['package']))

    except market.RateLimitException, e:
        logging.warn("Hit rate limit!  Pausing for 5 minutes...")

    except Exception, e:
        logging.critical("App {} raised exception {}".format(
            next_app['package'].encode('ascii', 'ignore'), e))
        logging.critical("Account: {} ({})".format(
            next_account['username'], next_account['id']))

    logging.debug("Finished working with {} at {}".format(
        next_app['package'].encode('ascii', 'ignore'), 
        datetime.datetime.now()))


if __name__ == '__main__':
    main()
