import cherrypy
import webbrowser
import threading
import traceback
import fitbit
import datetime
import time
import math
import itertools
import sys
from oauthlib.oauth2.rfc6749.errors import MismatchingStateError, MissingTokenError
from configclass import configclass, config_from_file
from funcy import partial
from PyTlin import k

ATTR_ACCESS_TOKEN = 'access_token'
ATTR_REFRESH_TOKEN = 'refresh_token'
ATTR_CLIENT_ID = 'client_id'
ATTR_CLIENT_SECRET = 'client_secret'
ATTR_LAST_SAVED_AT = 'last_saved_at'

FITBIT_CONFIG_FILE = 'fitbit.conf'
DEFAULT_CONFIG = {
    ATTR_CLIENT_ID: 'CLIENT_ID_HERE',
    ATTR_CLIENT_SECRET: 'CLIENT_SECRET_HERE',
    ATTR_LAST_SAVED_AT: 0
}
CHERRYPY_URL = 'http://127.0.0.1:8080/'

class OAuth2Server:
    def __init__(self, client_id, client_secret,
                 redirect_uri=CHERRYPY_URL):
        """ Initialize the FitbitOauth2Client """
        self.success_html = """
            <h1>You are now authorized to access the Fitbit API!</h1>
            <br/><h3>You can close this window</h3>"""
        self.failure_html = """
            <h1>ERROR: %s</h1><br/><h3>You can close this window</h3>%s"""

        self.fitbit = fitbit.Fitbit(
            client_id,
            client_secret,
            redirect_uri=redirect_uri,
            timeout=10,
        )

    def browser_authorize(self):
        """
        Open a browser to the authorization url and spool up a CherryPy
        server to accept the response
        """
        url, _ = self.fitbit.client.authorize_token_url()
        # Open the web browser in a new thread for command-line browser support
        threading.Timer(1, webbrowser.open, args=(url,)).start()
        cherrypy.quickstart(self)

    @cherrypy.expose
    def index(self, state, code=None, error=None):
        """
        Receive a Fitbit response containing a verification code. Use the code
        to fetch the access_token.
        """
        error = None
        if code:
            try:
                self.fitbit.client.fetch_access_token(code)
            except MissingTokenError:
                error = self._fmt_failure(
                    'Missing access token parameter.</br>Please check that '
                    'you are using the correct client_secret')
            except MismatchingStateError:
                error = self._fmt_failure('CSRF Warning! Mismatching state')
        else:
            error = self._fmt_failure('Unknown error while authenticating')
        # Use a thread to shutdown cherrypy so we can return HTML first
        self._shutdown_cherrypy()
        return error if error else self.success_html

    def _fmt_failure(self, message):
        tb = traceback.format_tb(sys.exc_info()[2])
        tb_html = '<pre>%s</pre>' % ('\n'.join(tb)) if tb else ''
        return self.failure_html % (message, tb_html)

    def _shutdown_cherrypy(self):
        """ Shutdown cherrypy in one second, if it's running """
        if cherrypy.engine.state == cherrypy.engine.states.STARTED:
            threading.Timer(1, cherrypy.engine.exit).start()




class FitBitAPI(configclass):
    def __init__(self):
        config_file = self.load_config_file(FITBIT_CONFIG_FILE,DEFAULT_CONFIG)

        if config_file:
            self.client_id = config_file[ATTR_CLIENT_ID]
            self.client_secret = config_file[ATTR_CLIENT_SECRET]

            #check if config file contains tokens if not load them and save
            if None in (config_file.get(ATTR_ACCESS_TOKEN,None),
                                    config_file.get(ATTR_REFRESH_TOKEN,None)):
                server = OAuth2Server(self.client_id, self.client_secret)
                server.browser_authorize()
                token = server.fitbit.client.session.token
                config_file = self.save_token(token)

            self.authd_client = fitbit.Fitbit(config_file[ATTR_CLIENT_ID],
                                config_file[ATTR_CLIENT_SECRET],
                                access_token=config_file[ATTR_ACCESS_TOKEN],
                                refresh_token=config_file[ATTR_REFRESH_TOKEN],
                                expires_at=config_file[ATTR_LAST_SAVED_AT],
                                refresh_cb=self.save_token)
            self.authd_client.API_VERSION = 1.2

    def save_token(self, token):
        config_contents = {
            ATTR_ACCESS_TOKEN: token['access_token'],
            ATTR_REFRESH_TOKEN: token['refresh_token'],
            ATTR_CLIENT_ID: self.client_id,
            ATTR_CLIENT_SECRET: self.client_secret,
            ATTR_LAST_SAVED_AT: int(time.time())
        }
        return config_from_file(FITBIT_CONFIG_FILE, config_contents)

    def request_app_setup(self):
        print("Please create a Fitbit developer app at https://dev.fitbit.com/apps/new.\
                           For the OAuth 2.0 Application Type choose Personal.\
                           Set the Callback URL to {}.\
                           They will provide you a Client ID and secret.\
                           These need to be saved into the file located at: {}.\
                           Then come back here and hit the below button.\
                           ".format(CHERRYPY_URL, FITBIT_CONFIG_FILE))

    def limited_date_API_call(self, base_date,end_date,func):
        #I'm assuming that a func call counts as end_date-base_date+1 API calls
        '''This function tries to call func(date1,date2) where the range
         (date1,date2) is as large a the API Rate Limit allows
        it returns the remaining range of dates'''

        #first check if the tracker is initialized, otherwise make a simple
        #activities request
        remaining_requests = self.authd_client.FitbitRateLimitRemaining
        if remaining_requests == None:
            self.authd_client.activities()
            remaining_requests = int(self.authd_client.FitbitRateLimitRemaining)
        else:
            remaining_requests = int(remaining_requests)

        #now split the date range into remaining_requests chunks, take the first
        # and convert into list of dates
        date_delims = self.split_dates_in_Ns(base_date,end_date,remaining_requests)
        first_date_delim = date_delims[0]


        #finally we appy func to the first_date_delim's
        func(first_date_delim['base_date'],first_date_delim['end_date'])
        #and return the remaining range of dates, which can be inserted back
        #to this function once the rate limit resets
        return (date_delims[1]['base_date'], date_delims[-1]['end_date']) if \
            len(date_delims)>1 else None



    def _get_date_str(self, date):
        return date if isinstance(date,str) else date.strftime('%Y-%m-%d')

    def _get_date_obj(self, datestr):
        return datestr if isinstance(datestr,datetime.datetime) else \
                                datetime.datetime.strptime(datestr,'%Y-%m-%d')

    def _sleep_struct(self,list):
        struct = {}
        [struct[x['dateOfSleep']].append(x) if struct.get(x['dateOfSleep'])
                else struct.update({x['dateOfSleep']:[x]}) for x in list]
        return struct

    def _heart_struct(self,list):
        struct = {}
        [struct.update({x['dateTime']:x}) for x in list['activities-heart']]
        return struct

    def _intraday_heart_struct(self,list):
        struct = {}
        [struct.update({x['activities-heart'][0]['dateTime']:x}) for x in list]
        return struct

    def split_dates_in_Ns(self, base_date, end_date, N):
        bd = self._get_date_obj(base_date)
        ed = self._get_date_obj(end_date)
        daydiff = 1 + (ed-bd).days
        if daydiff > 0:
            n = math.floor(daydiff/N)
            return list(map(lambda x,y:
             {'base_date': self._get_date_str(bd + datetime.timedelta(days=x)),
              'end_date': self._get_date_str(bd + datetime.timedelta(days=y))},
                                                [0]+[i*N for i in range(1,n+1)],
                                    [i*N-1 for i in range(1,n+1)]+[daydiff-1]))
        else:
            return [{'base_date': self._get_date_str(base_date),
                                    'end_date': self._get_date_str(end_date)}]

    def date_delimiter_to_range(self, base_date, end_date):
        bd = self._get_date_obj(base_date)
        ed = self._get_date_obj(end_date)
        daydiff = 1 + (ed-bd).days
        return [self._get_date_str(bd + datetime.timedelta(days=x))
                                                    for x in range(0, daydiff)]

    def get_heartrate_info(self, base_date = None, end_date = None):
        return self._heart_struct(self.authd_client.time_series('activities/heart',
                                        base_date=base_date, end_date=end_date))

    def get_intraday_heartrate_info(self, base_date = 'today',
                                end_date = '1d',  detail_level = '1min'):
        if end_date == '1d':
            return self._intraday_heart_struct([
                self.authd_client.intraday_time_series('activities/heart',
                base_date=base_date, detail_level = detail_level)])
        else:
            list_dates = self.date_delimiter_to_range(base_date, end_date)
            return k(list_dates) @ partial(map, lambda date:
             self.get_intraday_heartrate_info(base_date = date,
                                end_date = '1d', detail_level = detail_level))\
             @ list @ \
             (lambda lst: {list(x.keys())[0]: list(x.values())[0] for x in lst})\
              @ 'end'

    def get_sleep_info(self, base_date = None, end_date = None):
        list_dates = self.split_dates_in_Ns(base_date, end_date, 100)
        return k(list_dates) @ partial(map,
         lambda x: self.authd_client.time_series('sleep',
                base_date=x['base_date'], end_date=x['end_date'])['sleep']) \
         @ itertools.chain.from_iterable @ list @ self._sleep_struct \
         @ 'end'

    def update_heart_intraday(self,base_date,heartintradayfile, end_date=None):
        bdate = self._get_date_str(base_date)
        today = self._get_date_str(end_date) if end_date else \
                                self._get_date_str(datetime.datetime.today())

        return self.limited_date_API_call(bdate,today,
         lambda bd,ed: config_from_file(heartintradayfile,
         self.get_intraday_heartrate_info(base_date=bd, end_date=ed,
                                            detail_level = '1sec'),update=True))

    def update_heart_sleep(self, base_date, heartfile, sleepfile, end_date=None):
        today = self._get_date_str(end_date) if end_date else \
                                self._get_date_str(datetime.datetime.today())
        bd = self._get_date_str(base_date)

        config_from_file(heartfile,
                self.get_heartrate_info(base_date=bd, end_date=today),update=True)

        config_from_file(sleepfile,
                    self.get_sleep_info(base_date=bd, end_date=today),update=True)
