import os

import numpy as np
import pandas as pd
import math
import os
import sys
import time
import utm


def load_data(filename, DATA_DIR):
    fname = os.path.join(DATA_DIR, filename)
    data = pd.read_csv(fname, header=3)

    data['Latitude (Decimal Degrees)'].dropna(inplace=True)
    data['Longitude (Decimal Degrees)'].dropna(inplace=True)

    data['Latitude (Decimal Degrees)'] = data['Latitude (Decimal Degrees)'].astype(
        float)
    data['Longitude (Decimal Degrees)'] = data['Longitude (Decimal Degrees)'].astype(
        float)

    data['dec_deg_latlon'] = data[[
        'Latitude (Decimal Degrees)', 'Longitude (Decimal Degrees)']].values.tolist()

    # convert decimal degrees to utm and make new columns for UTM Northing and Easting
    data['utm_latlon'] = [utm.from_latlon(
        e[0], e[1]) for e in data['dec_deg_latlon']]

    data['utm_E'] = [e[0] for e in data['utm_latlon']]
    data['utm_N'] = [e[1] for e in data['utm_latlon']]

    return data
