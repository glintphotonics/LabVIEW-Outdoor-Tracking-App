from astral_parse import AstralPositions
from razon_parse import RaZON
import pytz
import datetime as dt
import timezonefinder
import math
import pandas as pd
import matplotlib.pyplot as plt
from Tkinter import Tk
from tkFileDialog import askopenfilename
from util_funcs import *
from angle_to_position import *
import argparse

parser = argparse.ArgumentParser(description='Choose saved dataframes from file')
parser.add_argument('-i', action='store_true')
options = parser.parse_args()
if options.i:
    from_file=True
else:
    from_file=False


def main():
    interp_points = 5
    i = 4

    now = dt.datetime.now() - dt.timedelta(days=2)
    # Samples data between two datetime objects (date is supplied by )
    start = dt.datetime(year=now.year, 
                        month=now.month, 
                        day=now.day, 
                        hour=10, 
                        minute=15, 
                        second=0)
    end = dt.datetime(year=now.year, 
                      month=now.month, 
                      day=now.day, 
                      hour=16, 
                      minute=0, 
                      second=0)

    # Astral parse
    pacific_tz = pytz.timezone('US/Pacific')
    ap = AstralPositions(lat=37.595912, lon=-122.368835)
    # print(ap.get_altitude(), ap.get_azimuth())
    local_start = pacific_tz.localize(start)
    local_end = pacific_tz.localize(end)
    azimuth_df = ap.get_azimuth_angles(start=local_start, end=local_end)
    altitude_df = ap.get_altitude_angles(start=local_start, end=local_end)
    altitude_angles = altitude_df['Angle (deg)']
    azimuth_angles = azimuth_df['Angle (deg)']
    zenith_angles = altitude_angles.apply(lambda x: 90-x)
    # print(zenith_angles, altitude_angles)
    datetimes = altitude_df['Datetime Local']
    # print(zenith_angles, azimuth_angles)
    azimuth_angles_rad = azimuth_angles.map(math.radians)
    zenith_angles_rad = zenith_angles.map(math.radians)
    altitude_angles_rad = altitude_angles.map(math.radians)
    solar_angles_df = pd.DataFrame({'Azimuth (rad)': azimuth_angles_rad, 
                                    'Altitude (rad)': altitude_angles_rad,
                                    'Datetime Local': datetimes})
    # print(cos_correct_df)
    # astral_positions = ap.get_position_from_angle(solar_angles_df, num_interp_points=4)
    # print(astral_positions)


    # Communicate to RaZON through local webpage
    razon = RaZON(lat=37.595932, lon=-122.368848, panel_tilt=20, razonIP="192.168.15.150")
    data = razon.request_interval(now, start, end)
    razon_azimuth_angles, razon_altitude_angles = data['Azimuth (rad)'], data['Altitude (rad)']

    # razon_dni_df, razon_azimuth_angles, razon_altitude_angles = data
    # positions = razon.get_position_from_angle(data, start, end, num_interp_points=4)
    # print(razon_dni_df.columns)

    # Plotting
    # Astral Azimuth plotted against RaZON Azimuth
    # fig, ax = plt.subplots()
    # ax.set_title('Azimuth Comparison')
    # astral_az_line = ax.plot(azimuth_df['Datetime Local'], 
    #                          azimuth_df['Angle (deg)'],
    #                          label='Astral')
    # razon_az_line = ax.plot(data['Datetime Local'], 
    #                         razon_azimuth_angles.map(math.degrees), 
    #                         label='RaZON')
    # plt.xticks(rotation=45)
    # ax.legend()

    # # Astral Azimuth plotted against RaZON Azimuth
    # fig, ax = plt.subplots()
    # ax.set_title('Altitude Comparison')
    # astral_alt_line = ax.plot(altitude_df['Datetime Local'], 
    #                           altitude_df['Angle (deg)'],
    #                           label='Astral')
    # razon_az_line = ax.plot(data['Datetime Local'], 
    #                         razon_altitude_angles.map(math.degrees), 
    #                         label='RaZON')
    # plt.xticks(rotation=45)
    # ax.legend()

    # # Azimuth differences plotted over time
    # fig, ax = plt.subplots()
    # ax.set_title('Azimuth Comparison')
    # diffs = azimuth_df['Angle (deg)'] - razon_azimuth_angles.map(math.degrees)
    # diffs.map(abs)
    # razon_az_line = ax.plot(data['Datetime Local'], 
    #                         diffs, 
    #                         label='|RaZON - Astral|')
    # plt.xticks(rotation=45)
    # ax.legend()

    # # Altitude differences plotted over time
    # fig, ax = plt.subplots()
    # ax.set_title('Altitude Comparison')
    # diffs = altitude_df['Angle (deg)'] - razon_altitude_angles.map(math.degrees)
    # diffs.map(abs)
    # razon_az_line = ax.plot(data['Datetime Local'], 
    #                         diffs, 
    #                         label='|RaZON - Astral|')
    # plt.xticks(rotation=45)
    # ax.legend()


    # Generate Interpolated Data
    astral_positions = []
    positions = []
    interp_settings = []
    # for i in range(interp_points)[-1:]:
    # # for i in [6,7,8]:
    #     print('Generating interpolated data for %d points' % i)
    #     astral_pos = get_position_from_angle(solar_angles_df, ap.tilt, i)
    #     astral_positions.append(astral_pos)
    #     pos = get_position_from_angle(data, razon.tilt, i)
    #     positions.append(pos)
    #     setting = 'linear N={}'.format(i)
    #     interp_settings.append(setting)
    #     print('Done!')

    # Generating Cubic Interpolation Data
    # for i in range(interp_points)[-1:]:
    # for i in [1, interp_points]
    # for i in [6,7,8]:
    setting = 'cubic_N={}'.format(interp_points)
    start_iso = str(start.isoformat()).replace(':','')
    end_iso = str(end.isoformat()).replace(':','')
    if not from_file:
        astral_pos = get_position_from_angle(solar_angles_df, ap.tilt, i, 'cubic')
        astral_pos.to_csv('./dataframes/' + 'astral_pos_{}_{}-{}'.format(setting, 
                                                                         start_iso, 
                                                                         end_iso))
        pos = get_position_from_angle(data, razon.tilt, i, 'cubic')
        astral_pos.to_csv('./dataframes/' + 'pos_{}_{}-{}'.format(setting, 
                                                                  start_iso, 
                                                                  end_iso))
    else:
        Tk().withdraw()
        astral_filename = askopenfilename(title='Select the astral CSV to use for analysis...')
        print(astral_filename)
        astral_pos = pd.read_csv(astral_filename)
        razon_filename = askopenfilename(title='Select the razon CSV to use for analysis...')
        print(razon_filename)
        pos = pd.read_csv(razon_filename)

    interp_settings.append(setting)
    astral_positions.append(astral_pos)
    positions.append(pos)

    print(astral_pos.columns)
    print(pos.columns)

    # Radial difference plotted over time
    fig, ax = plt.subplots()
    ax.set_title('Position Difference Comparison')
    for setting, astral_pos, pos in zip(interp_settings, astral_positions, positions):
        diffs_x = (pos['Interp. X (mm)'] - astral_pos['Interp. X (mm)'])**2
        diffs_y = (pos['Interp. Y (mm)'] - astral_pos['Interp. Y (mm)'])**2
        radial_diffs = (diffs_x + diffs_y).map(math.sqrt)
        razon_az_line = ax.plot(data['Datetime Local'], 
                                radial_diffs, 
                                label='sqrt((RaZON - Astral)^2) {}'.format(setting))
    plt.xticks(rotation=45)
    ax.legend()

    # X Position plotted over time
    fig, ax = plt.subplots()
    ax.set_title('X Position Comparison')
    for setting, astral_pos, pos in zip(interp_settings, astral_positions, positions):
        razon_x_line = ax.plot(data['Datetime Local'], 
                                pos['Interp. X (mm)'], 
                                label='RaZON {}'.format(setting))
        astral_x_line = ax.plot(data['Datetime Local'], 
                                astral_pos['Interp. X (mm)'], 
                                label='Astral {}'.format(setting))
        razon_x_line = ax.plot(data['Datetime Local'], 
                                pos['Fitted X Interp. (mm)'], 
                                label='RaZON {}'.format(setting))
        astral_x_line = ax.plot(data['Datetime Local'], 
                                astral_pos['Fitted X Interp. (mm)'], 
                                label='Astral {}'.format(setting))
    plt.xticks(rotation=45)
    ax.legend()

    # Y Position plotted over time
    fig, ax = plt.subplots()
    ax.set_title('Y Position Comparison')
    for setting, astral_pos, pos in zip(interp_settings, astral_positions, positions):
        razon_x_line = ax.plot(data['Datetime Local'], 
                                pos['Interp. Y (mm)'], 
                                label='RaZON {}'.format(setting))
        astral_x_line = ax.plot(data['Datetime Local'], 
                                astral_pos['Interp. Y (mm)'], 
                                label='Astral {}'.format(setting))
        razon_x_line = ax.plot(data['Datetime Local'], 
                                pos['Fitted Y Interp. (mm)'], 
                                label='RaZON {}'.format(setting))
        astral_x_line = ax.plot(data['Datetime Local'], 
                                astral_pos['Fitted Y Interp. (mm)'], 
                                label='Astral {}'.format(setting))
    plt.xticks(rotation=45)
    ax.legend()




    plt.show()


if __name__ == '__main__':
    print()
    main()