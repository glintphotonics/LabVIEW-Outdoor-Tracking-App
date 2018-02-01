#!/usr/bin/env python

# Script to be called by a parent at a constant rate

import matplotlib.pyplot as plt
import datetime as dt
import math
import numpy as np
import requests
from requests.exceptions import ConnectionError
import pandas as pd
import sys
if sys.version_info[0] < 3: 
    from StringIO import StringIO
else:
    from io import StringIO
import csv
import socket
import ast

# Config Settings
latitude = math.radians(37.595932)
longitude = math.radians(-122.368848)
tilt = math.radians(20)
dzenith = latitude-tilt
razonIP = "192.168.15.150"

def convert_float(x):
    try:
        x = float(x)
    except ValueError as e:
        print("Couldn't convert {} to a float.".format(x))
    return x

if __name__ == '__main__':

    try:
        # assert(1 < len(sys.argv) <= 2, 'Provide exactly one argument to script (Too many).')
        # assert(1 < len(sys.argv), 'Provide exactly one argument to script (Too little).')
        samplePeriodMinutes = sys.argv[1]
        # assert(60 <= samplePeriodMinutes, 'Sampling frequency of DNI should be greater than 60 sec.')
        # assert(int(samplePeriodMinutes), 'Provide an integer argument to script.')
        samplePeriodMinutes = int(samplePeriodMinutes)
    except Exception:
        raise

    # Date handling for request
    now = dt.datetime.now()
    # now = dt.datetime(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=0, second=0)
    print("Getting DNI data for {}...".format(now.date()))

    nowDateOutputFileString = now.strftime('%Y%m%d')
    nowDateString = now.strftime('%Y-%m-%d')
    nowDateFileGETString = now.strftime('%m-%d-%y')
    payload = {'beginDate':nowDateString,
               'endDate': nowDateString, 
               'fileName':str(nowDateFileGETString)+'.csv'}


    # Search for RaZON+
    # mac = [22, 445, 548, 631]
    # linux = [20, 21, 22, 23, 25, 80, 111, 443, 445, 631, 993, 995]
    # windows = [135, 137, 138, 139, 445]
    # aios = [49152, 62078] # Apple iOS (ios is also the name for Cisco's OS running on their products)

    # import subprocess
    # import sys
     
    # ip = '192.168.15.112'
        
    # # ping ip
    # p = subprocess.Popen(['ping', ip], stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE)
     
    # out, err = p.communicate()
     
    # # arp list
    # p = subprocess.Popen(['arp', '-n', ip], stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE)
     
    # out, err = p.communicate()
     
    # try:
    #     arp = [x for x in out.split('\n') if ip in x][0]
    #     print(arp)
    # except IndexError:
    #     print("Error")
    #     sys.exit(1)     # no arp entry found


    # socket_obj = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    # socket.setdefaulttimeout(1)
    # possible_connects = []
    # result = socket_obj.connect_ex(('192.168.15.112',22))
    # print(result, socket.getfqdn('192.168.15.112'), socket.gethostbyaddr("192.168.15.112"), socket_obj.getsockname(), socket.gethostname())

    # for addr in ['192.168.15.'+str(i) for i in range(0, 255)]:
    #     try:
    #         result = socket_obj.connect_ex((addr,22))
    #         if result == 0:
    #             possible_connects.append(addr)
    #     except:
    #         print("Error")
    # socket_obj.close()
    # print(possible_connects)
    # sys.exit(0)


    # Make request to RaZON for data, handle connection error
    try:
        r5 = requests.get("http://"+str(razonIP)+"/loggings/exportdata.csv", data=payload)
        # print('Solar angle request: {}'.format(r5.content))
    except ConnectionError:
        raise
    try:
        r6 = requests.get("http://"+str(razonIP)+"/status_trackings/lastirradiance?")
        # print('Last Irradiance request: {}'.format(r6.content))
    except ConnectionError:
        raise

    # Convert into readable csv and data
    sio = StringIO(r5.content)
    reader = csv.reader(r5.content)
    with open('results.csv', 'w+') as f:
        f.write(r5.content)
    dni_df = pd.read_csv("results.csv", skiprows=5)
    dni_df = dni_df.rename(columns={'IrrDirect (W/m2)':'Irrid. (W/m2)', 
                                              'Time Local ( hh:mm ) ':'Time (hh:mm:ss)'})
    irrid_arr = ast.literal_eval(r6.content)
    if irrid_arr:
        irrid_arr = irrid_arr[0]
    irrid = [convert_float(i) for i in irrid_arr][-3]


    # Get appropriate row (current minute data)
    times = dni_df['Time (hh:mm:ss)']
    hours = samplePeriodMinutes / 60
    startMinutes = (now.minute - samplePeriodMinutes) % 60
    if startMinutes == 59:
        hours += 1
    startHours = now.hour - hours
    # seconds = samplePeriodMinutes % 60
    start = dt.datetime(year=1900, 
                        month=1, 
                        day=1, 
                        hour=startHours, 
                        minute=startMinutes, 
                        second=now.second)
    print(start)
    greaterThanStart = (pd.to_datetime(times, format=' %H:%M:%S') > pd.to_datetime(start))
    end = dt.datetime(year=1900, 
                      month=1, 
                      day=1, 
                      hour=now.hour, 
                      minute=now.minute, 
                      second=now.second)
    lessThanEnd = (pd.to_datetime(times, format=' %H:%M:%S') <= pd.to_datetime(end))
    print(end)
    dni_df = dni_df[greaterThanStart & lessThanEnd]
    dni_df = dni_df.reset_index()
    # print(dni_df)
    # print(len(dni_df.index))
    if len(dni_df.index) == 0:
        sys.exit(0)

    # Solar angles used for cosine correction
    azimuth_angles = (dni_df['SolarAzimuth (Degrees)']).map(math.radians)
    altitude_angles = (90. - dni_df['SolarZenith (Degrees)']).map(math.radians)

    # Calculation of cos correction factors
    dni_df['Cos(Theta)'] = altitude_angles.map(math.cos)*azimuth_angles.map(math.sin)
    dni_df['Cos(Phi)'] = (math.sin(tilt)*altitude_angles.map(math.sin) + 
                               math.cos(tilt)*altitude_angles.map(math.cos)*
                               azimuth_angles.map(math.cos))
    dni_df['Theta_'] = 90.0 - dni_df['Cos(Theta)'].map(math.acos).map(math.degrees)
    dni_df['Phi_'] = 90.0 - dni_df['Cos(Phi)'].map(math.acos).map(math.degrees)
    dni_df['Cos(Theta)'] = dni_df['Theta_'].map(math.radians).map(math.cos)
    dni_df['Cos(Phi)'] = dni_df['Phi_'].map(math.radians).map(math.cos)

    # Apply cos correciton to irradiance
    illumination = dni_df['Irrid. (W/m2)']
    dni_df['Cosine Corrected DNI'] = illumination*(dni_df['Cos(Theta)']*
                                                   dni_df['Cos(Phi)'])
    # print(dni_df['Cos(Theta)'])
    # print(dni_df['Cos(Phi)'])
    irrid = irrid*float(dni_df['Cos(Theta)'])*float(dni_df['Cos(Phi)'])

    # print(dt.datetime.strptime(dni_df['Time (hh:mm:ss)'].ix[0], ' %H:%M:%S'), 
    #       float(dni_df['Cosine Corrected DNI']))
    # print(dni_df)
    print(float(dni_df['Theta_']), 
          float(dni_df['Phi_']),
          dni_df['Time (hh:mm:ss)'].ix[0][1:], 
          float(irrid))