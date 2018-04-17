#!/usr/bin/env python

import pymongo
from pymongo import MongoClient
import datetime as dt
import pytz
import pandas as pd


class QPD_DB_Parse():
    # Parsing object for stored MongoDB QPD data

    def __init__(self, ip_or_url, port):
        # MongoDB Logging
        self.mongo_client = MongoClient(ip_or_url, port)
        self.tracking_db = self.mongo_client.qpd_sensor
        self.tz = pytz.timezone('US/Pacific')

    def get_data_interval(self, start_dt, end_dt, tz=pytz.timezone('US/Pacific')):
        # Get QPD data from MongoDB
        diode_values = self.tracking_db.diode_values
        diode_values = diode_values.with_options(codec_options=CodecOptions(tz_aware=True, 
                                                                            tzinfo=tz))
        positions = self.tracking_db.requested_positions
        positions = positions.with_options(codec_options=CodecOptions(tz_aware=True, 
                                                                      tzinfo=tz))
        sensor_values = diode_values.find({'datetime': {'$gte': start_dt, '$lte': end_dt}})
        positions = positions.find({'datetime': {'$gte': start_dt, '$lte': end_dt}})
        sensor_values = list(sensor_values)
        positions = list(positions)

        # for v in sensor_values:
        #     print(v)
        # for p in positions:
        #     print(p)
        # print(len(sensor_values), len(positions))

        return sensor_values, positions

def to_df(list_db_entries):
    return pd.DataFrame(list_db_entries)


def main():
    pacific_tz = pytz.timezone('US/Pacific')
    start = pacific_tz.localize(dt.datetime(2018, 4, 9, 13, 45, 0, 0))
    end = pacific_tz.localize(dt.datetime(2018, 4, 9, 16, 0, 0, 0))
    parser = QPD_DB_Parse("192.168.15.7", 27017)
    sensor_vals, positions = parser.get_data_interval(start, end)
    print(start)
    print(end)
    sensor_vals, positions = to_df(sensor_vals), to_df(positions)
    # print(positions)

if __name__ == '__main__':
    main()