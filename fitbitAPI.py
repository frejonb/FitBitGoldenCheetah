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
			self.client_id = config_file.get(ATTR_CLIENT_ID)
			self.client_secret = config_file.get(ATTR_CLIENT_SECRET)

			#check if config file contains tokens if not load them and save
			if None in (config_file.get(ATTR_ACCESS_TOKEN,None), config_file.get(ATTR_REFRESH_TOKEN,None)):
				server = OAuth2Server(self.client_id, self.client_secret)
				server.browser_authorize()
				token = server.fitbit.client.session.token
				config_file = self.save_token(token)

			self.authd_client = fitbit.Fitbit(config_file.get(ATTR_CLIENT_ID),config_file.get(ATTR_CLIENT_SECRET),access_token=config_file.get(ATTR_ACCESS_TOKEN),refresh_token=config_file.get(ATTR_REFRESH_TOKEN),expires_at=config_file.get(ATTR_LAST_SAVED_AT), refresh_cb=self.save_token)
			self.authd_client.API_VERSION = 1.2


	def save_token(self, token):
		config_contents = {
			ATTR_ACCESS_TOKEN: token.get('access_token'),
			ATTR_REFRESH_TOKEN: token.get('refresh_token'),
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

	def split_dates_in_Ns(self, base_date, end_date, N):
		bd = datetime.datetime.strptime(base_date,'%Y-%m-%d')
		ed = datetime.datetime.strptime(end_date,'%Y-%m-%d')
		daydiff = 1 + (ed-bd).days
		if daydiff > 0:
			n = math.floor(daydiff/N)
			return list(map(lambda x,y: {'base_date': (bd + datetime.timedelta(days=x)).strftime('%Y-%m-%d'), 'end_date': (bd + datetime.timedelta(days=y)).strftime('%Y-%m-%d')}, [0]+[i*N for i in range(1,n+1)],[i*N-1 for i in range(1,n+1)]+[daydiff-1]))
		else:
			return [{'base_date': base_date, 'end_date': end_date}]

	def get_heartrate_info(self, base_date = None, end_date = None):
		return self.authd_client.time_series('activities/heart',base_date=base_date, end_date=end_date)

	def get_sleep_info(self, base_date = None, end_date = None):
		list_dates = self.split_dates_in_Ns(base_date, end_date, 100)
		return {'sleep': list(itertools.chain.from_iterable(map(lambda x: self.authd_client.time_series('sleep',base_date=x.get('base_date'), end_date=x.get('end_date')).get('sleep'), list_dates)))}
