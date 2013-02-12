import market_pb2
import urllib
import urllib2
import base64
import zlib

API_URL = "https://android.clients.google.com/market/api/ApiRequest"
LOGIN_URL = "https://www.google.com/accounts/ClientLogin"
ACCOUNT_TYPE = "HOSTED_OR_GOOGLE"
PROTOCOL_VERSION = 2
SDK_VERSION = "passion:9"
CARRIER = "T-Mobile"
CARRIER_CODE = "310260"
USER_LANGUAGE = "en"
USER_COUNTRY = "us"


class NotAuthenticatedException(Exception): pass
class LoginException(Exception): pass
class SearchException(Exception): pass
class UnknownResponseException(Exception): pass


class Market(object):
    def __init__(self, auth_token=None, android_id=None):
        """ Constructor optionally accepts auth_token and account's associated
        android_id to continue a previously authenticated session.  Otherwise
        initialize with no parameters and use the login method. """
        if auth_token and android_id:
            self.auth_token = auth_token
            self.android_id = android_id

    def __prepare_request(self):
        if not self.auth_token:
            raise NotAuthenticatedException("")
        request = market_pb2.Request()
        request.context.authSubToken = self.auth_token
        request.context.isSecure = True
        request.context.version = 2009011
        request.context.androidId = self.android_id
        request.context.deviceAndSdkVersion = SDK_VERSION
        request.context.userLanguage = USER_LANGUAGE
        request.context.userCountry = USER_COUNTRY
        request.context.operatorAlpha = CARRIER
        request.context.simOperatorAlpha = CARRIER
        request.context.operatorNumeric = CARRIER_CODE
        request.context.simOperatorNumeric = CARRIER_CODE
        return request

    def __send_proto(self, request):
        """ Sends a Protocol Buffers Request object """
        params = {
                'version': PROTOCOL_VERSION,
                'request': base64.b64encode(request.SerializeToString()),
                }
        headers = {
                'User-Agent': 'Android-Market/2 (sapphire PLAT-RC33); gzip',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Cookie': 'ANDROIDSECURE={}'.format(self.auth_token),
                }
        httpreq = urllib2.Request(API_URL, urllib.urlencode(params), headers)
        content = urllib2.urlopen(httpreq).read()
        ungzipped_content = zlib.decompress(content, 16 + zlib.MAX_WBITS)
        response = market_pb2.Response.FromString(ungzipped_content)
        return response

    def login(self, username, password, android_id, service="androidsecure", 
            account_type=ACCOUNT_TYPE):
        params = {
                'Email': username,
                'Passwd': password,
                'service': service,
                'accountType': account_type
                }
        headers = {
                'User-Agent': 'Android-Market/2 (sapphire PLAT-RC33); gzip',
                }
        httpreq = urllib2.Request(LOGIN_URL, urllib.urlencode(params), headers)
        content = urllib2.urlopen(httpreq).read()
        auth_results = dict([x.split('=') for x in content.splitlines()])
        self.android_id = android_id
        self.auth_token = auth_results['Auth']
        return self.auth_token

    def get_app_info(self, query_string):
        """ Accepts a package name of a specific Android app (in com.*) format
        and returns useful package info and download links as a dict. """
        request = self.__prepare_request()

        # Create RequestGroup for AppsRequest
        reqgroup = request.requestgroup.add()
        reqgroup.appsRequest.query = query_string
        reqgroup.appsRequest.startIndex = 0
        reqgroup.appsRequest.entriesCount = 10
        reqgroup.appsRequest.withExtendedInfo = True
        # Create RequestGroup for GetAssetRequest
        reqgroup = request.requestgroup.add()
        reqgroup.getAssetRequest.assetId = query_string

        try:
            response = self.__send_proto(request)
            # Only get the part of the response we're interested in
            app = response.responsegroup[0].appsResponse.app[0]
            asset = response.responsegroup[1].getAssetResponse.installasset[0]
        except urllib2.HTTPError, e:
            if e.code == 400:
                raise SearchException("Package not found")
            elif e.code == 403:
                raise NotAuthenticatedException("")
            else:
                raise
        except IndexError, e:
            raise SearchException("Package not found")

        return {
                'id': asset.assetId,
                'creator': app.creatorId,
                'name': asset.assetName,
                'package': asset.assetPackage,
                'version': app.versionCode,
                'version_string': app.version,
                'rating': app.rating,
                'ratings_count': app.ratingsCount,
                'file_size': asset.assetSize,
                'download_url': asset.blobUrl,
                'cookie_name': asset.downloadAuthCookieName,
                'cookie_value': asset.downloadAuthCookieValue,
                }

    def download(self, app_info, save_as=None):
        """ Accepts app_info response from get_app_info method and downloads
        to the path specified in save_as (or uses com.package.apk as default).
        Returns the save_as path where file was written when successful. """
        opener = urllib2.build_opener()
        opener.addheaders.append(('Cookie', '{}={}'.format(
            app_info['cookie_name'], app_info['cookie_value'])))
        opener.addheaders.append(('User-Agent', 
            'Android-Market/2 (sapphire PLAT-RC33); gzip'))
        f = opener.open(app_info['download_url'])
        # If save_as path is not defined, save to local path using package name
        # as the filename.
        if not save_as:
            save_as = "{}.apk".format(app_info['package'])
        open(save_as, 'w').write(f.read())
        return save_as
