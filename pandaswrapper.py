import pandas as pd
from funcy import walk_values, partial
from configclass import config_from_file
from PyTlin import k

def dictsOfDicts_to_dataframes(dod):
    dict_of_dfs = walk_values(pd.DataFrame, dod)
    return pd.concat(dict_of_dfs.values(), axis=1, keys=dict_of_dfs.keys())

def sleep_time_series(speepfile = 'sleep.txt'):
    sleepinfo = config_from_file(speepfile)
    return pd.DataFrame([{'dateOfSleep': sp['dateOfSleep'],
        'minutesAsleep': sp['minutesAsleep']} for sp in sleepinfo['sleep']])

def intraday_hr_dataframe(heartfile = 'heartrate-intraday.txt'):
    hr = config_from_file(heartfile)
    return dictsOfDicts_to_dataframes({info['activities-heart'][0]['dateTime']:
        info['activities-heart-intraday']['dataset']
                                            for info in hr})



def intraday_hr_series_for_sleepmin(minAsleepCond, sleepfile = 'sleep.txt',
                                        heartfile = 'heartrate-intraday.txt'):
    sleepts = sleep_time_series(sleepfile)
    dates = list(sleepts[minAsleepCond(sleepts.minutesAsleep)].dateOfSleep)
    intra_hr = intraday_hr_dataframe(heartfile)

    return intra_hr.loc[:,dates]
