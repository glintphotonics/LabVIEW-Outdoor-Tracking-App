# Astral solar angles parse

import datetime as dt
from astral import Astral, Location
import pytz
import timezonefinder
import pymongo
from pymongo import MongoClient
# from razon_parse import get_cos_factors
import math
import pandas as pd
from angle_to_position import *

class AstralPositions:

    def __init__(self, lat, lon, panel_tilt=20, session_id=None, ip_or_url='192.168.15.7', 
                 port=27017):
        # Date/wall time attributes
        if session_id == None:
            import uuid
            self.session_id = uuid.uuid1()
        self.a = Astral()
        self.timezone_string = 'US/Pacific'

        # Timezone from lat/lng
        tzfinder = timezonefinder.TimezoneFinder()
        self.tz = tzfinder.certain_timezone_at(lat=lat, lng=lon)
        self.location = Location(('Burlingame',
                                  'Pacific West',
                                  lat,
                                  lon,
                                  self.timezone_string,
                                  6.1
                                  ))
        self.sun = self.location.sun(date=dt.datetime.today().date(), local=True)
        print(self.sun)

        # MongoDB Tracking
        self.mongo_client = MongoClient(ip_or_url, port)
        self.db = self.mongo_client.astral

        # Tilt of theoretical panel
        self.tilt = math.radians(panel_tilt)

    def get_now_local(self):
        now = dt.datetime.now()
        localtime = pytz.timezone(self.tz)
        now_local = localtime.localize(now)
        return now_local

    @staticmethod
    def perdelta(start, end, delta):
        curr = start
        while curr <= end:
            yield curr
            curr += delta

    def get_azimuth(self, dt_local=None):
        if dt_local == None:
            dt_local = self.get_now_local()
        angle = self.location.solar_azimuth(dt_local)
        return angle

    def get_altitude(self, dt_local=None):
        if dt_local == None:
            dt_local = self.get_now_local()
        angle = self.location.solar_elevation(dt_local)
        return angle

    def _angular_doc(self):
        datetime = self.get_now_local()
        alt = self.get_curr_altitude(datetime)
        az = self.get_curr_azimuth(datetime)
        doc = {"altitude": alt,
               "azimuth": az,
               "datetime": datetime,
               "sessionid": self.session_id}
        solar_angles = self.db.solar_angles
        _id = solar_angles.insert_one(doc).inserted_id

    def collect_angular_data(period=2):
        pass

    def get_azimuth_angles(self, start, end, frequency=60, continuous=True):
        td = dt.timedelta(seconds=frequency)
        # datetimes = [start + i*td for i in ]
        # delta = end-start
        datetimes = list(self.perdelta(start, end, td))
        angles = [self.get_azimuth(d) for d in datetimes]
        angles = pd.DataFrame({'Datetime Local':datetimes, 'Angle (deg)':angles})
        # while datetime <= end:
        #     start
        if not continuous:
            pass
        return angles

    def get_altitude_angles(self, start, end, frequency=60, continuous=True):
        td = dt.timedelta(seconds=frequency)
        # datetimes = [start + i*td for i in ]
        datetimes = list(self.perdelta(start, end, td))        
        angles = [self.get_altitude(d) for d in datetimes]
        angles = pd.DataFrame({'Datetime Local':datetimes, 'Angle (deg)':angles})
        # while datetime <= end:
        #     start
        if not continuous:        
            pass
        return angles

    def get_solar_angles(self, start, end):
        local_start = self.tz.localize(start)
        local_end = self.tz.localize(end)
        azimuth_df = self.get_azimuth_angles(start=local_start, end=local_end)
        altitude_df = self.get_altitude_angles(start=local_start, end=local_end)
        altitude_angles = altitude_df['Angle (deg)']
        azimuth_angles = azimuth_df['Angle (deg)']
        zenith_angles = altitude_angles.apply(lambda x: 90-x)
        datetimes = altitude_df['Datetime Local']
        azimuth_angles_rad = azimuth_angles.map(math.radians)
        zenith_angles_rad = zenith_angles.map(math.radians)
        altitude_angles_rad = altitude_angles.map(math.radians)
        cos_correct_df = ap.get_cos_factors(azimuth_angles_rad, zenith_angles_rad)
        solar_angles_df = pd.DataFrame({'Azimuth (rad)': azimuth_angles_rad, 
                                        'Altitude (rad)': altitude_angles_rad,
                                        'Datetime Local': datetimes})
        return solar_angles_df

def main():
    # Astral parse
    pacific_tz = pytz.timezone('US/Pacific')
    ap = AstralPositions(lat=37.595912, lon=-122.368835)
    # print(ap.get_altitude(), ap.get_azimuth())
    start = pacific_tz.localize(dt.datetime(2018, 4, 9, 13, 45, 0, 0))
    end = pacific_tz.localize(dt.datetime(2018, 4, 9, 16, 0, 0, 0))
    azimuth_df = ap.get_azimuth_angles(start=start, end=end)
    altitude_df = ap.get_altitude_angles(start=start, end=end)
    altitude_angles = altitude_df['Angle (deg)']
    azimuth_angles = azimuth_df['Angle (deg)']
    zenith_angles = altitude_angles.apply(lambda x: 90-x)
    # print(zenith_angles, altitude_angles)
    datetimes = altitude_df['Datetime Local']
    # print(zenith_angles, azimuth_angles)
    azimuth_angles_rad = azimuth_angles.map(math.radians)
    zenith_angles_rad = zenith_angles.map(math.radians)
    altitude_angles_rad = altitude_angles.map(math.radians)
    cos_correct_df = ap.get_cos_factors(azimuth_angles_rad, zenith_angles_rad)
    solar_angles_df = pd.DataFrame({'Azimuth (rad)': azimuth_angles_rad, 
                                    'Altitude (rad)': altitude_angles_rad,
                                    'Datetime Local': datetimes})
    # print(cos_correct_df)
    astral_positions = ap.get_position_from_angle(solar_angles_df)
    print(astral_positions)


if __name__ == '__main__':
    print('Starting...')
    main()

