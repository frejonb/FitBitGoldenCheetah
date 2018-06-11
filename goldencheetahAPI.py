from configclass import configclass, config_from_file
from funcy import partial, select, filter, last
from more_itertools import flatten, split_before
import pandas as pd
from datetime import datetime
import os
from PyTlin import k
from copy import deepcopy

ATTR_GC_FOLDER = 'gc_folder'
GC_CONFIG_FILE = 'gc.conf'

DEFAULT_CONFIG = {
    ATTR_GC_FOLDER: 'GOLDECHEETAH_ATHLETE_FOLDER_PATH_HERE',
}



class GoldenCheetahAPI(configclass):
    def __init__(self):
        config_file = self.load_config_file(GC_CONFIG_FILE,DEFAULT_CONFIG)

        if config_file:
            self.gc_folder_path = config_file[ATTR_GC_FOLDER]
            self.activities_path = os.path.join(self.gc_folder_path,'activities')
            self.jsonfiles = [os.path.join(self.activities_path, f)
                                    for f in os.listdir(self.activities_path)]
            self.activities = map(config_from_file, self.jsonfiles)

    def request_app_setup(self):
	    print("The GoldenCheetah athlete's folder needs to be saved into the\
         file located at: {}.".format(GC_CONFIG_FILE))

    def get_power_history(self):
        path = os.path.join(self.gc_folder_path,'config/power.zones')
        with open(path, 'r') as fdesc:
        	lines = fdesc.read().splitlines()

        return k(lines) \
         @ partial(map,lambda x: x.split(':')) @ flatten \
         @ partial(split_before, pred = lambda x: 'DEFAULTS' in x or '/' in x) \
         @ list @ partial(select, lambda x: x[0]!='DEFAULTS') \
         @ (lambda l: [{'dateTime': datetime.strptime(x[0],'%Y/%m/%d'),
            **( k(x[1:]) @ partial(map,lambda y:
             k(y.split('=')) @ partial(map, lambda i: i.strip()) @ tuple @ 'end'
                                                            if '=' in y else y)
                @ dict @ 'end' ) } for x in l ]) @ 'end'

    def get_power_at_date(self, date):
        return k(self.get_power_history()) \
         @ partial(filter, lambda x:
                        x['dateTime'] < datetime.strptime(date,'%Y-%m-%d'))\
         @ last @ 'end'

    def filter_activities(self, pred):
        return filter(pred, deepcopy(self.activities))


    def get_rides_with_note(self, note):
        return self.filter_activities(lambda x:
                                            note in x['RIDE']['TAGS']['Notes'])

    def get_rides_by_date(self, datestr, datestr_end=None):
        date = datetime.strptime(datestr,'%Y-%m-%d').date()
        date_end = datetime.strptime(datestr_end,'%Y-%m-%d').date() \
                                                        if datestr_end else None
        def ride_datestr_to_date(x):
            return datetime.strptime(x['RIDE']['STARTTIME'].strip(),
                                                 '%Y/%m/%d %H:%M:%S %Z').date()

        return self.filter_activities(
            lambda x:(ride_datestr_to_date(x) >= date) \
                  and (ride_datestr_to_date(x) <= date_end) if date_end else \
                                                date == ride_datestr_to_date(x))


    def ride_to_intervals(self,dic):
    	return k(dic) @ (lambda ride:
         k(ride['RIDE']['INTERVALS']) @ partial(map, lambda interval:
         k(ride['RIDE']['SAMPLES'])
          @ partial(filter, lambda data:
          data['SECS'] >= interval['START'] and data['SECS'] < interval['STOP'])
          @	partial(map, lambda data:
            {'SECS': data.get('SECS'),'WATTS': data.get('WATTS'),
                                                        'HR': data.get('HR')})
          @ list
          @ (lambda x: (interval['NAME'], x)) @ 'end'
                                                       ) @ dict @ 'end') @ 'end'
