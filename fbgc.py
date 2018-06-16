# %%
import os
%matplotlib inline
import pandas as pd
import matplotlib.pyplot as plt
from fitbitAPI import FitBitAPI
from goldencheetahAPI import GoldenCheetahAPI
import pandaswrapper as pdw
from configclass import config_from_file
from funcy import compose, partial, select, walk_values
from PyTlin import k
import datetime
import numpy as np
import glob
from more_itertools import flatten

#Fetch FitBit data
base_date = '2017-01-26' #end_date = '2018-06-11'

fbApi = FitBitAPI()
## Heartrate and sleep info
# fbApi.update_heart_sleep(base_date,'heartrate.txt', 'sleep.txt')

## API Request limit on heartrate intraday info
#
# try:
#     remaining_range = fbApi.update_heart_intraday(base_date,'heartrate')
# except :
#     pass
#
# remaining_range = ('2018-05-25', '2018-06-11')
#
# try:
#     remaining_range = fbApi.update_heart_intraday(remaining_range[0],
#                             'heartrate-intraday',end_date = remaining_range[1])
# except:
#     pass
#
# remaining_range
#
# config_from_file('heartrate-intraday.txt',
#         list(flatten(map(config_from_file, glob.glob('heartrate-intraday*')))))





# load from files
config_from_file()
heartrateinfo = config_from_file('heartrate.txt')
heartrateintradayinfo = config_from_file('heartrate-intraday.txt')
sleepinfo = config_from_file('sleep.txt')

sleepts = pdw.sleep_time_series('sleep.txt')
#transpose, set dates as columns and sum values of same column name (nore than 1 sleep time per day)
lel = sleepts.transpose()
lel.columns =  lel.head(1).iloc[0,:]
lel = lel.reindex(lel.index.drop('dateOfSleep'))
lel.columns.name = None
lel = lel.groupby(lel.columns, axis = 1).sum()
lel
lel.axes
# I want to add the above to the table below
sts2 = pdw.intraday_hr_series_for_sleepmin(lambda x: x<= 240)
sts2.axes
pd.concat([sts2],keys=['foo'], names=['firstlevel'])

sts2

pd.concat([sts2,sleepts])


pd.concat([sts2,sleepts.reset_index().T], keys=[1,2])
pdw.intraday_hr_dataframe().plot()






#Fetch GoldeCheetah data
gcApi = GoldenCheetahAPI()

gcApi.get_power_at_date('2017-02-11')


pop=gcApi.get_rides_with_note('trainerroad')
pop
pop.__sizeof__()
lal = next(pop)
lal

pep = gcApi.get_rides_by_date('2017-03-09', datestr_end = '2017-03-28')
len(list(pep))

pup = gcApi.get_rides_with_note('sloten')
pupu = list(pup)

len(pupu)

pupu[1]['RIDE']['STARTTIME']
dict([('jue', 1),('lol',2)])
gcApi.ride_to_intervals(pupu[0])
pipu = pdw.dictsOfDicts_to_dataframes(gcApi.ride_to_intervals(pupu[0]))
pipu

pipui = pipu.iloc[:,pipu.columns.get_level_values(0) == 'Lap 1 '].get('Lap 1 ').set_index('SECS').reindex(k(pipui.index) @ (lambda x: np.arange(x.min(),x.max()+1)) @ 'end', fill_value = 0)

pipui.plot()
.plot()
pipu.iloc[:,pipu.columns.get_level_values(0) == 'Lap 1 '].plot()

pipu.iloc[:,pipu.columns.get_level_values(0) == 'Lap 1 ']



gcApi.get_power_history()



# %%
# ===========================================
lal = pd.read_json('heartrate.txt')
lal = pd.DataFrame(
 compose(list,
 partial(map, lambda x:
     [ x['dateTime'], x['value']['restingHeartRate']])
                                        )(heartrateinfo.get('activities-heart'))
 , columns = ['dateTime', 'restingHeartRate'])

lal[lal.dateTime > '2018-06-01'].plot()
