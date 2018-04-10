#!/usr/bin/env python 

from cos_correct_v2 import *
from angle_to_position import *
import pandas as pd
import datetime as dt

def get_position_from_angle(razon, data, start, end):
    # Obtain cos factors and corrected data
    dni_df, altitude_angles, azimuth_angles = data
    cos_correct_df = razon.get_cos_factors(altitude_angles, azimuth_angles)
    dni_df = razon.cos_correct(dni_df, cos_correct_df)
    print(dni_df)

    angles = pd.DataFrame()
    angles['Theta'] = dni_df['Theta_']
    angles['Phi'] = dni_df['Phi_']
    angles['Time'] = dni_df['Time (hh:mm:ss)']
    print(angles)

    def match_angles_wrapper(angles):
        mapping = read_and_clean_angle_position()
        return (match_angles(mapping, angles[0], angles[1]), angles[2])

    positions = angles.apply(match_angles_wrapper, axis=1)
    print(positions)
    positions = [(x[0], x[1], y) for (x, y) in positions]
    positions = zip(*positions)
    print(positions)
    positions = pd.DataFrame(positions).transpose()
    print(positions)
    return positions

def main():
    # Communicate to RaZON through local webpage
    razon = RaZON(lat=37.595932, lon=-122.368848, panel_tilt=20, razonIP="192.168.15.150")
    # Use RaZON.get_local_datetime
    now = razon.get_local_datetime() - dt.timedelta(days=1)

    # Samples data between two datetime objects (date is supplied by )
    start = dt.datetime(year=1900, month=1, day=1, hour=13, minute=45, second=0)
    end = dt.datetime(year=1900, month=1, day=1, hour=16, minute=0, second=0)
    data = razon.request_interval(now, start, end)
    positions = get_position_from_angle(razon, data, start, end)

    # # Loop through appropriate angles:
    # for angle in angles:
    #     mapping = read_and_clean_angle_position()
    #     x, y = match_angles(mapping, theta, phi)

if __name__ == '__main__':
    main()
