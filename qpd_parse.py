#!/usr/bin/env python

import pymongo
from pymongo import MongoClient
import datetime as dt
import pytz
from bson.codec_options import CodecOptions


class QPDDBParse():
    def __init__(self, ip_or_url):
        # MongoDB Logging
        self.mongo_client = MongoClient(ip_or_url, 27017)
        self.tracking_db = self.mongo_client.qpd_sensor
        self.tz = pytz.timezone('US/Pacific')
        self.options = CodecOptions(tz_aware=True)

    def get_data_interval(self, start_dt, end_dt, tz=pytz.timezone('US/Pacific')):
        # diode_values = tracking_db.get_collection('diode_values', codec_options=options)
        # positions = tracking_db.get_collection('requested_positions', codec_options=options)
        diode_values = self.tracking_db.diode_values
        diode_values = diode_values.with_options(codec_options=CodecOptions(tz_aware=True, 
                                                                tzinfo=tz))
        positions = self.tracking_db.requested_positions
        positions = positions.with_options(codec_options=CodecOptions(tz_aware=True, 
                                                                      tzinfo=tz))
        sensor_values = diode_values.find({'datetime': {'$gte': start_dt, '$lt': end_dt}})
        positions = positions.find({'datetime': {'$gte': start_dt, '$lt': end_dt}})
        sensor_values = list(sensor_values)
        positions = list(positions)

        for v in sensor_values:
            print(v)
        for p in positions:
            print(p)

        print(len(sensor_values), len(positions))


def main():
    start = dt.datetime(2018, 4, 9, 0, 0, 0, 0)
    end = dt.datetime(2018, 4, 9, 23, 59, 59, 0)
    parser = QPDDBParse("192.168.15.7")
    data = parser.get_data_interval(start, end)


if __name__ == '__main__':
    main()