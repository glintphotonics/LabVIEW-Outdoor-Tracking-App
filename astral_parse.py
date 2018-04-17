# Astral solar angles parse

import datetime as dt
from astral import Astral, Location
import pytz
import timezonefinder
import pymongo
from pymongo import MongoClient


class AstralPositions:

    def __init__(self, lat, lon, session_id=None):
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

    def get_now_local(self):
        now = dt.datetime.now()
        localtime = pytz.timezone(self.tz)
        now_local = localtime.localize(now)
        return now_local

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


def main():
    ap = AstralPositions(lat=37.595912, lon=-122.368835)
    print(ap.get_curr_altitude(), ap.get_curr_azimuth())



if __name__ == '__main__':
    main()

