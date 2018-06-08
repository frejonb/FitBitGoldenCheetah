import os
%matplotlib inline
import pandas as pd
import matplotlib.pyplot as plt
from fitbitAPI import FitBitAPI
from goldencheetahAPI import GoldenCheetahAPI
from configclass import config_from_file



#Fetch FitBit data
if not os.path.isfile('heartrate.txt') and not os.path.isfile('sleep.txt'):
	base_date = '2017-01-26'
	end_date = '2018-06-07'
	fbApi = FitBitAPI()
	config_from_file('heartrate.txt', fbApi.get_heartrate_info(base_date=base_date, end_date=end_date))
	config_from_file('sleep.txt', fbApi.get_sleep_info(base_date=base_date, end_date=end_date))

# load from files
heartrateinfo = config_from_file('heartrate.txt')
sleepinfo = config_from_file('sleep.txt')


#Fetch GoldeCheetah data
gcApi = GoldenCheetahAPI()

gcApi.get_power_at_date('2017-02-11')




# ===========================================
lal = pd.read_json('heartrate.txt')
lal = pd.DataFrame(list(map(lambda x: [ x.get('dateTime'), x.get('value').get('restingHeartRate')] ,heartrateinfo.get('activities-heart'))), columns = ['dateTime', 'restingHeartRate'])

lal[lal.dateTime > '2018-06-01'].plot()
