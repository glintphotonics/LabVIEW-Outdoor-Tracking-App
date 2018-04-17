from qpd_parse import QPD_DB_Parse, to_df
from razon_parse import RaZON
import matplotlib.pyplot as plt
import datetime as dt
import pytz
import re

def norm_series(series):
    return (series - series.mean()) / (series.max() - series.min())

def main():
    # Communicate to RaZON through local webpage
    razon = RaZON(lat=37.595932, lon=-122.368848, panel_tilt=20, razonIP="192.168.15.150")
    now = dt.datetime(2018, 4, 9)
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
    razon_positions = razon.get_position_from_angle(data, start, end)
    dni_df, altitude_angles, azimuth_angles = data
    cos_correct_df = razon.get_cos_factors(altitude_angles, azimuth_angles)
    dni_df = razon.cos_correct(dni_df, cos_correct_df)


    # QPD Parse
    pacific_tz = pytz.timezone('US/Pacific')
    start = pacific_tz.localize(dt.datetime(2018, 4, 9, 13, 45, 0, 0))
    end = pacific_tz.localize(dt.datetime(2018, 4, 9, 16, 0, 0, 0))
    parser = QPD_DB_Parse("192.168.15.7", 27017)
    sensor_vals, positions = parser.get_data_interval(start, end)
    sensor_vals, positions = to_df(sensor_vals), to_df(positions)

    # PLOTS
    # Compare qpd and razon x positions
    fig, ax = plt.subplots()
    ax.set_title('X Position Comparison')
    razon_line = ax.plot(razon_positions['Datetime Local'], -razon_positions['X'], label='RaZON')
    qpd_plot = ax.plot(positions['datetime'], positions['x_position'], label='QPD')
    qpd_scatter = ax.plot_date(positions['datetime'], positions['x_position'], 
                               c='orange', 
                               alpha=0.6,
                               label='QPD')
    ax.legend()

    # Compare qpd and razon y positions
    fig, ax = plt.subplots()
    ax.set_title('Y Position Comparison')
    razon_line = ax.plot(razon_positions['Datetime Local'], -razon_positions['Y'], label='RaZON')
    qpd_plot = ax.plot(positions['datetime'], positions['y_position'], label='QPD')
    qpd_scatter = ax.plot_date(positions['datetime'], positions['y_position'], 
                               c='orange', 
                               alpha=0.6, 
                               label='QPD')
    ax.legend()

    # Display Detector voltages over time
    fig, ax = plt.subplots()
    ax.set_title('Detector voltages vs. Time')
    print(sensor_vals.columns)
    sensor_cols = [re.match('sensor[0-9]', col) for col in sensor_vals.columns]
    sensor_cols = [col.group() for col in sensor_cols if col != None]
    print(sensor_cols)
    for sensor_i in sensor_cols:
        ax.plot(sensor_vals['datetime'], sensor_vals[sensor_i])
    ax.legend()

    # Display detector signals (voltages with differencing math) over time
    fig, ax = plt.subplots()
    ax.set_title('Detector signals vs. Time')
    sum_sensor_vals = sum([sensor_vals[col] for col in sensor_cols])
    y_tmp = (sensor_vals['sensor2'] + \
             sensor_vals['sensor3']) - (sensor_vals['sensor1'] + \
                                        sensor_vals['sensor4'])
    sensor_vals['y_signals'] = y_tmp / sum_sensor_vals
    x_tmp = (sensor_vals['sensor3'] + \
             sensor_vals['sensor4']) - (sensor_vals['sensor1'] + \
                                        sensor_vals['sensor2'])
    sensor_vals['x_signals'] = x_tmp / sum_sensor_vals
    ax.plot(sensor_vals['datetime'], sensor_vals['x_signals'])
    ax.plot(sensor_vals['datetime'], sensor_vals['y_signals'])
    ax.legend()

    #
    fig, ax = plt.subplots()
    ax.set_title('Signal/Detector Correlation over Time')
    for sensor_i in sensor_cols:
        sensor = sensor_vals[sensor_i]
        sensor_vals[sensor_i+'_norm'] = norm_series(sensor)
        ax.plot(sensor_vals['datetime'], sensor_vals[sensor_i+'_norm'], alpha=0.5)
    x_sig = sensor_vals['x_signals']
    y_sig = sensor_vals['y_signals']
    sensor_vals['x_signals_norm'] = norm_series(x_sig)
    sensor_vals['y_signals_norm'] = norm_series(y_sig)
    ax.plot(sensor_vals['datetime'], sensor_vals['x_signals_norm'], c='blue')
    ax.plot(sensor_vals['datetime'], sensor_vals['y_signals_norm'], c='red')
    ax.legend()

    #
    fig, ax = plt.subplots()
    ax.set_title('Signal/Position Correlation over Time')
    positions['x_position_norm'] = norm_series(-positions['x_position'])
    positions['y_position_norm'] = norm_series(-positions['y_position'])
    ax.plot_date(positions['datetime'], positions['x_position_norm'], c='blue')
    ax.plot_date(positions['datetime'], positions['y_position_norm'], c='red')
    ax.plot(sensor_vals['datetime'], sensor_vals['x_signals_norm'], c='blue', alpha=0.2)
    ax.plot(sensor_vals['datetime'], sensor_vals['y_signals_norm'], c='red', alpha=0.2)
    ax.legend()

    #
    fig, ax = plt.subplots()
    ax.set_title('All Signals over Time')
    y_tmp = (sensor_vals['sensor2'] + \
             sensor_vals['sensor3']) - (sensor_vals['sensor1'] + \
                                        sensor_vals['sensor4'])
    x_tmp = (sensor_vals['sensor3'] + \
             sensor_vals['sensor4']) - (sensor_vals['sensor1'] + \
                                        sensor_vals['sensor2'])
    z_tmp = (sensor_vals['sensor1'] + \
             sensor_vals['sensor3']) - (sensor_vals['sensor2'] + \
                                        sensor_vals['sensor4'])
    w_tmp = (sensor_vals['sensor2'] + \
             sensor_vals['sensor4']) - (sensor_vals['sensor1'] + \
                                        sensor_vals['sensor3'])
    x_tmp = x_tmp / sum_sensor_vals
    y_tmp = y_tmp / sum_sensor_vals
    z_tmp = z_tmp / sum_sensor_vals
    w_tmp = w_tmp / sum_sensor_vals
    ax.plot(sensor_vals['datetime'], y_tmp, label='2+3-1+4')
    ax.plot(sensor_vals['datetime'], x_tmp, label='3+4-1+2')
    ax.plot(sensor_vals['datetime'], z_tmp, label='1+3-2+4')
    ax.plot(sensor_vals['datetime'], w_tmp, label='2+4-1+3')
    ax.legend()

    #
    fig, ax = plt.subplots()
    ax.set_title('Signals/DNI vs. Time')
    ax.plot(sensor_vals['datetime'], sensor_vals['x_signals_norm'])
    ax.plot(sensor_vals['datetime'], sensor_vals['y_signals_norm'])
    razon_dates = dni_df['Datetime Local']
    cos_corrected_dni = dni_df['Irrad. (W/m2)']*dni_df['Cos(Theta)']*dni_df['Cos(Phi)']
    cos_corrected_diff = dni_df['IrrDiffuse (W/m2)']*dni_df['Cos(Theta)']*dni_df['Cos(Phi)']
    cos_corrected_dni_norm = norm_series(cos_corrected_dni)
    cos_corrected_diff_norm = norm_series(cos_corrected_diff)
    ax.plot(razon_dates, cos_corrected_dni_norm)
    ax.plot(razon_dates, cos_corrected_diff_norm)
    ax.legend()
    print('Correlation of IrrDiff w. Y signal: {}'.format(cos_corrected_diff.corr(sensor_vals['y_signals'])))
    print('Correlation of IrrDiff w. X signal: {}'.format(cos_corrected_diff.corr(sensor_vals['x_signals'])))
    print('Correlation of IrrDirect w. Y signal: {}'.format(cos_corrected_dni.corr(sensor_vals['y_signals'])))
    print('Correlation of IrrDirect w. X signal: {}'.format(cos_corrected_dni.corr(sensor_vals['x_signals'])))




    plt.show()



if __name__ == '__main__':
    main()

