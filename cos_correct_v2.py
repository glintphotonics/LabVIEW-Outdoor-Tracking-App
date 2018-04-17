#!/usr/bin/env python

# Script to be called by a parent at a constant rate

import matplotlib.pyplot as plt
import datetime as dt
import math
import numpy as np
import requests
from requests.exceptions import ConnectionError, RequestException
import pandas as pd
import sys
if sys.version_info[0] < 3: 
    from StringIO import StringIO
else:
    from io import StringIO
import csv
import socket
import ast
import time
import pytz
import timezonefinder



def convert_float(x):
    try:
        x = float(x)
    except ValueError as e:
        print("Couldn't convert {} to a float.".format(x))
    return x


class RaZON():
    def __init__(self, lat, lon, panel_tilt=20, razonIP="192.168.15.150"):
        # Config Settings
        latitude = math.radians(lat)
        longitude = math.radians(lon)
        self.tilt = math.radians(panel_tilt)
        dzenith = latitude-panel_tilt
        self.razonIP = razonIP

        # Timezone from lat/lng
        tzfinder = timezonefinder.TimezoneFinder()
        self.tz = tzfinder.certain_timezone_at(lat=lat, lng=lon)

    def get_local_datetime(self):
        # Date handling for request
        now = dt.datetime.now()
        localtime = pytz.timezone(self.tz)
        a = localtime.localize(now)
        is_dst = bool(a.dst())

        # RaZON doesn't adjust for DST
        if is_dst:
            now = now.replace(hour=now.hour-1)
        print("Getting DNI data for {}...".format(now.date()))
        return now

    def sample_interval(self, df, start, end):
        # Get appropriate time slice
        # If multiple spans of days, return time slices in each day
        # times = df['Time (hh:mm:ss)']
        # dates = df['Date Local (yyyy-mm-dd)']
        df_datetimes = df['Datetime Local (non-DST)']
        # RaZON doesn't adjust for DST
        # Request for an hour earlier if date lies in DST
        localtime = pytz.timezone(self.tz)

        # start_dst = localtime.localize(start).dst()
        # end_dst = localtime.localize(end).dst()
        # is_start_dst = bool(start_dst)
        # is_end_dst = bool(end_dst)
        # if is_start_dst:
        #     start = start.replace(hour=start.hour-1)
        # if is_end_dst:
        #     end = end.replace(hour=end.hour-1)

        # Slice data by start and end time and return the dataframe
        # start = start.replace(year=1900, month=1, day=1)
        # end = end.replace(year=1900, month=1, day=1)

        dst_datetimes = df_datetimes.apply(lambda x: bool(localtime.localize(x).dst()))
        # print(df)
        df['Datetime Local'] = df[dst_datetimes]['Datetime Local (non-DST)'] + \
                                         dt.timedelta(hours=1)
        # print(df)
        corrected_datetimes = df['Datetime Local']
        # greaterThanStart = (pd.to_datetime(times, format=' %H:%M:%S') > pd.to_datetime(start))
        # lessThanEnd = (pd.to_datetime(times, format=' %H:%M:%S') <= pd.to_datetime(end))
        greaterThanStart = corrected_datetimes > start
        # print(greaterThanStart.iloc[0])
        lessThanEnd = corrected_datetimes <= end
        # print(lessThanEnd.iloc[0])
        time.sleep(0.2)
        df = df[greaterThanStart & lessThanEnd]
        # print(df)
        df = df.reset_index()
        return df

    def sample_data(self, df, end_time, duration, time_col_name):
        # Get appropriate row (current minute data)
        times = df[time_col_name]
        hours = duration / 60
        startMinutes = (end_time.minute - duration) % 60
        if startMinutes == 59:
            hours += 1
        startHours = end_time.hour - hours
        start = dt.datetime(year=1900, 
                            month=1, 
                            day=1, 
                            hour=startHours, 
                            minute=startMinutes, 
                            second=end_time.second)
        greaterThanStart = (pd.to_datetime(times, format=' %H:%M:%S') > pd.to_datetime(start))
        end = dt.datetime(year=1900, 
                          month=1, 
                          day=1, 
                          hour=end_time.hour, 
                          minute=end_time.minute, 
                          second=end_time.second)
        lessThanEnd = (pd.to_datetime(times, format=' %H:%M:%S') <= pd.to_datetime(end))
        time.sleep(0.5)
        df = df[greaterThanStart & lessThanEnd]
        df = df.reset_index()
        return df

    def request_interval(self, now, start, end):
        # nowDateOutputFileString = now.strftime('%Y%m%d')
        start_date = start.date()
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end.date()
        end_date = end_date.strftime('%Y-%m-%d')
        nowDateFileGETString = now.strftime('%m-%d-%y')
        payload = {'beginDate' : start_date,
                   'endDate' : end_date, 
                   'fileName' : str(nowDateFileGETString)+'.csv'}

        # Make request to RaZON for data, handle connection error
        try:
            req = requests.get("http://"+str(self.razonIP)+"/loggings/exportdata.csv",data=payload)
        except RequestException as e:
            raise e

        # Convert into readable csv and data
        sio = StringIO(req.content)
        reader = csv.reader(req.content)
        with open('results.csv', 'w+') as f:
            f.write(req.content)
        dni_df = pd.read_csv("results.csv", skiprows=5)
        dni_df = dni_df.rename(columns={'IrrDirect (W/m2)':'Irrad. (W/m2)', 
                                        'Time Local ( hh:mm ) ':'Time (hh:mm:ss)'})
        times, dates = dni_df['Time (hh:mm:ss)'], dni_df['Date Local (yyyy-mm-dd)']
        df_datetimes = times+dates
        df_datetimes = pd.to_datetime(df_datetimes, format=' %H:%M:%S %Y-%m-%d')
        dni_df['Datetime Local (non-DST)'] = df_datetimes
        dni_df = self.sample_interval(dni_df, start, end)

        # Solar angles used for cosine correction
        azimuth_angles = (dni_df['SolarAzimuth (Degrees)']).map(math.radians)
        altitude_angles = (90. - dni_df['SolarZenith (Degrees)']).map(math.radians)

        return dni_df, azimuth_angles, altitude_angles

    def request_data(self, now, end_time, duration):
        nowDateOutputFileString = now.strftime('%Y%m%d')
        nowDateString = now.strftime('%Y-%m-%d')
        nowDateFileGETString = now.strftime('%m-%d-%y')
        payload = {'beginDate':nowDateString,
                   'endDate': nowDateString, 
                   'fileName':str(nowDateFileGETString)+'.csv'}

        # Make request to RaZON for data, handle connection error
        try:
            r5 = requests.get("http://"+str(self.razonIP)+"/loggings/exportdata.csv", data=payload)
        except RequestException as e:
            raise e
        try:
            r6 = requests.get("http://"+str(self.razonIP)+"/status_trackings/lastirradiance?")
        except RequestException as e:
            raise e

        # Convert into readable csv and data
        sio = StringIO(r5.content)
        reader = csv.reader(r5.content)
        with open('results.csv', 'w+') as f:
            f.write(r5.content)
        dni_df = pd.read_csv("results.csv", skiprows=5)
        dni_df = dni_df.rename(columns={'IrrDirect (W/m2)':'Irrad. (W/m2)', 
                                        'Time Local ( hh:mm ) ':'Time (hh:mm:ss)'})
        dni_df = self.sample_data(dni_df, end_time, duration, 'Time (hh:mm:ss)')

        irrad_arr = ast.literal_eval(r6.content)
        if irrad_arr:
            irrad_arr = irrad_arr[0]
        irrad = [convert_float(i) for i in irrad_arr][-3]

        # Solar angles used for cosine correction
        azimuth_angles = (dni_df['SolarAzimuth (Degrees)']).map(math.radians)
        altitude_angles = (90. - dni_df['SolarZenith (Degrees)']).map(math.radians)

        return dni_df, azimuth_angles, altitude_angles

    def get_cos_factors(self, azimuth_angles, altitude_angles):
        cos_correct_df = pd.DataFrame()
        # Calculation of cos correction factors
        cos_correct_df['Cos(Theta)'] = altitude_angles.map(math.cos)*azimuth_angles.map(math.sin)
        cos_correct_df['Cos(Phi)'] = (math.sin(self.tilt)*altitude_angles.map(math.sin) + 
                              math.cos(self.tilt)*altitude_angles.map(math.cos)*
                              azimuth_angles.map(math.cos))
        cos_correct_df['Theta_'] = 90.0 - cos_correct_df['Cos(Theta)'].map(math.acos).map(math.degrees)
        cos_correct_df['Phi_'] = 90.0 - cos_correct_df['Cos(Phi)'].map(math.acos).map(math.degrees)
        cos_correct_df['Cos(Theta)'] = cos_correct_df['Theta_'].map(math.radians).map(math.cos)
        cos_correct_df['Cos(Phi)'] = cos_correct_df['Phi_'].map(math.radians).map(math.cos)
        return cos_correct_df

    def cos_correct(self, dni_df, cos_correct_df):
        # Apply cos correction to irradiance
        illumination = dni_df['Irrad. (W/m2)']
        dni_df['Cosine Corrected DNI'] = illumination*(cos_correct_df['Cos(Theta)']*
                                                       cos_correct_df['Cos(Phi)'])
        # dni_df = dni_df.append(cos_correct_df)
        for col in cos_correct_df.columns:
            dni_df[col] = pd.Series(cos_correct_df[col], index=dni_df.index)
        return dni_df

    def get_position_from_angle(self, data, start, end):
        # Obtain cos factors and corrected data
        dni_df, altitude_angles, azimuth_angles = data
        cos_correct_df = self.get_cos_factors(altitude_angles, azimuth_angles)
        dni_df = self.cos_correct(dni_df, cos_correct_df)
        # print(dni_df)

        angles = pd.DataFrame()
        angles['Theta'] = dni_df['Theta_']
        angles['Phi'] = dni_df['Phi_']
        # angles['Time'] = dni_df['Time (hh:mm:ss)']
        # angles['Datetime Local'] = dni_df['Datetime Local']
        # print(angles)

        def match_angles_wrapper(angles):
            mapping = read_and_clean_angle_position()
            return match_angles(mapping, angles[0], angles[1])

        positions = angles.apply(match_angles_wrapper, axis=1)
        # print(positions)
        positions = [(x[0], x[1]) for x in positions]
        positions = zip(*positions)
        # print(positions)
        positions = pd.DataFrame(positions).transpose()
        positions['Datetime Local'] = dni_df['Datetime Local']
        # print(positions)
        return positions

def main():
    # Communicate to RaZON through local webpage
    razon = RaZON(lat=37.595932, lon=-122.368848, panel_tilt=20, razonIP="192.168.15.150")
    # Use RaZON.get_local_datetime
    # now = razon.get_local_datetime() - dt.timedelta(days=1)
    now = dt.datetime(2018, 4, 9)

    # Samples data between two datetime objects (date is supplied by )
    start = dt.datetime(year=now.year, 
                        month=now.month, 
                        day=now.day, 
                        hour=13, 
                        minute=45, 
                        second=0)
    end = dt.datetime(year=now.year, 
                      month=now.month, 
                      day=now.day, 
                      hour=16, 
                      minute=0, 
                      second=0)

    data = razon.request_interval(now, start, end)
    positions = razon.get_position_from_angle(data, start, end)
    print(positions)

def main1():
    razon = RaZON(lat=37.595932, lon=-122.368848, panel_tilt=20, razonIP="192.168.15.150")

    try:
        # assert(1 < len(sys.argv) <= 2, 'Provide exactly one argument to script (Too many).')
        # assert(1 < len(sys.argv), 'Provide exactly one argument to script (Too little).')
        samplePeriodMinutes = sys.argv[1]
        # assert(60 <= samplePeriodMinutes, 'Sampling frequency of DNI should be greater than 60 sec.')
        # assert(int(samplePeriodMinutes), 'Provide an integer argument to script.')
        samplePeriodMinutes = int(samplePeriodMinutes)
    except Exception:
        raise

    # Communicate to RaZON through local webpage
    now = razon.get_local_datetime()
    data = razon.request_data(now, now, samplePeriodMinutes)

    # Samples data from now back to samplePeriodMinutes
    # data = [sample_data(d, now, samplePeriodMinutes, 'Time (hh:mm:ss)') for d in data]
    dni_df, altitude_angles, azimuth_angles = data
    cos_correct_df = razon.get_cos_factors(altitude_angles, azimuth_angles)
    # print(cos_correct_df)
    # print(dni_df)
    dni_df = razon.cos_correct(dni_df, cos_correct_df)

    try:
        irrad = dni_df['Irrad. (W/m2)']
        irrad = irrad*float(dni_df['Cos(Theta)'])*float(dni_df['Cos(Phi)'])
        print(float(dni_df['Theta_']), 
              float(dni_df['Phi_']),
              dni_df['Time (hh:mm:ss)'].ix[0][1:], 
              float(irrad))
    except TypeError as e:
        print(dni_df)
        print("RaZON data not here yet...")


if __name__ == '__main__':
    # main1()
    main()