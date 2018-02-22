import os

import numpy as np
import pandas as pd
import math
import os
import sys
import time
import utm

from helper_functions import load_data

import logging
logging.config.fileConfig(os.path.join(LOGGING_DIR, 'logging.conf'))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data/')
LOGGING_DIR = os.path.join(BASE_DIR, 'logging/')


stn_df = load_data('Station_Inventory_EN.csv', DATA_DIR)


def make_dataframe(df, filename):

    return df.to_csv(filename)


def get_stations(lat, lon, radius):
    # input target location decimal degrees [lat, lon]
    target_loc = utm.from_latlon(lat, lon)
    # squamish_utm_loc = utm.from_latlon(49.796, -123.203)

    stn_df['distance_to_target'] = np.sqrt((stn_df['utm_E'] - squamish_utm_loc[0])**2 +
                                           (stn_df['utm_N'] - squamish_utm_loc[1])**2)

    # enter the distance from the target to search for stations
    search_radius = radius * 1000

    # pull the station IDs for all stations within 10km of stations
    target_stns = stn_df[stn_df['distance_to_target'] < search_radius]
    target_stns = target_stns.dropna(axis=0, how='any', subset=[
        'MLY First Year', 'MLY Last Year'])

    t_frame = 2  # 2 corresponds to daily, 1 to hourly, 3 to monthly
    # for hourly, need to add '&Day={}' back in following '&month={}'
    results = {}

    for index, row in target_stns.iterrows():
        rec_start = int(row['MLY First Year'])
        rec_end = int(row['MLY Last Year'])

        years = [e for e in range(rec_start, rec_end + 1)]
        frames = []
        all_data = pd.DataFrame()

        for year in years:
            ec_base_url = 'http://climate.weather.gc.ca/climate_data/bulk_data_e.html?'
            ec_url = ec_base_url + 'format=csv&stationID={}&Year={}&Month={}&Day=14&timeframe={}&submit=Download+Data'.format(
                row['Station ID'], year, 1, t_frame)

            df = pd.read_csv(ec_url, header=23, parse_dates=['Date/Time'])

            frames += [df]

        all_data = pd.concat(frames)

        stn_name = str(stn_df[stn_df['Station ID'] ==
                              row['Station ID']].Name.item())

        print('record for {} = {} to {}'.format(stn_name, rec_start, rec_end))

        results[stn_name] = {}

        stn_id = row['Station ID']).strip()
            new_file_name=os.path.join(DATA_DIR, stn_name + '_' +
            str(stn_id + '_ID' +
                str(rec_start) + '_to_' + str(rec_end) + '.csv')

        # update results dict object with desired parameters
        results[stn_name]['period_of_record'] = [rec_start, rec_end]
        results[stn_name]['station_name'] = stn_name
        results[stn_name]['station_ID'] = stn_id
        results[stn_name]['new_file_name'] = new_file_name
        results[stn_name]['data'] = all_data

        print('these are currently the results')
        print(results)
