from configclass import configclass
from funcy import compose, partial, select, filter, last
from more_itertools import flatten, split_before
from datetime import datetime

ATTR_GC_FOLDER = 'gc_folder'
GC_CONFIG_FILE = 'gc.conf'

DEFAULT_CONFIG = {
    ATTR_GC_FOLDER: 'GOLDECHEETAH_ATHLETE_FOLDER_PATH_HERE',
}



class GoldenCheetahAPI(configclass):
    def __init__(self):
        config_file = self.load_config_file(GC_CONFIG_FILE,DEFAULT_CONFIG)

        if config_file:
            self.gc_folder_path = config_file.get(ATTR_GC_FOLDER)

    def request_app_setup(self):
	    print("The GoldenCheetah athlete's folder needs to be saved into the file located at: {}.".format(GC_CONFIG_FILE))

    def get_power_history(self):
        path = self.gc_folder_path + '/config/power.zones'
        with open(path, 'r') as fdesc:
        	lines = fdesc.read().splitlines()

        return compose(\
          lambda l: [{'dateTime': datetime.strptime(x[0],'%Y/%m/%d'), \
              **compose(dict, partial(map, \
                lambda y: compose(tuple,partial(map, lambda i: i.strip()))(y.split('=')) \
                          if '=' in y else y))(x[1:])} for x in l ], \
          partial(select, lambda x: x[0]!='DEFAULTS'),list,\
          partial(split_before, pred = lambda x: 'DEFAULTS' in x or '/' in x),\
           flatten,\
           partial(map,lambda x: x.split(':')) \
           )(lines)

    def get_power_at_date(self, date):
        return compose(last, \
                  partial(filter, lambda x: x.get('dateTime') < datetime.strptime(date,'%Y-%m-%d')))\
                  (self.get_power_history())
