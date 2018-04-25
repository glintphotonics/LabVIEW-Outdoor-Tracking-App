#!/usr/bin/env python

import matplotlib.pyplot as plt
import matplotlib.mlab as mb
import numpy as np
import csv
import re
import math
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import pandas as pd
from pandas import DataFrame
import sys
from scipy.interpolate import interp1d, interp2d, griddata
from scipy.optimize import least_squares
from util_funcs import *


def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')

def f(x):
    determinant = 2500.00 - x**2
    if 2500.00 == x**2:
        # print('FUCK')
        # print(determinant)
        determinant = 0
    assert determinant >= 0, '{0} should be less than {1}'.format(x**2, 2500.00)
    return math.sqrt(determinant)

def read_and_clean_map():
    angleposition = pd.read_csv("../../Quad Detector/Reference/Gen1 1deg Angle Position Map.csv", 
                                index_col=0)
    # Reference adjustment (Focal Position vs. Solar Angle)
    # Flip axes of reference file (To make positive posisitions matchup with positive angles)
    angleposition["Theta"] = -angleposition["Theta"]
    angleposition["Phi"] = -angleposition["Phi"]
    return angleposition

def filter_angle_position(angleposition):
    # Filter angles for those with compound less than 50 deg
    # First Theta
    positive_theta = angleposition["Theta"] >= 0
    negative_theta = angleposition["Theta"] < 0
    theta_pos = angleposition[positive_theta]
    theta_neg = angleposition[negative_theta]
    cpd_less_than_50 = theta_pos["Theta"] <= map(f, theta_pos["Phi"])
    atheta_pos = theta_pos[cpd_less_than_50]
    _neghelp = map(f, theta_neg["Phi"])
    _neghelp = [-1 * item for item in _neghelp]
    cpd_less_than_50 = theta_neg["Theta"] >= _neghelp
    theta_neg = theta_neg[cpd_less_than_50]
    ref = pd.concat([theta_pos, theta_neg])

    # Then Phi
    positive_phi = ref["Phi"] >= 0
    negative_phi = ref["Phi"] < 0
    phi_pos = ref[positive_phi]
    phi_neg = ref[negative_phi]
    cpd_less_than_50 = phi_pos["Phi"] <= map(f,phi_pos["Theta"])
    phi_pos = phi_pos[cpd_less_than_50]
    _neghelp = map(f, phi_neg["Theta"])
    _neghelp = [-1 * item for item in _neghelp]
    cpd_less_than_50 = phi_neg["Phi"] >= _neghelp
    phi_neg = phi_neg[cpd_less_than_50]
    angle_position_map = pd.concat([phi_pos, phi_neg])
    # print_full(angle_position_map)
    return angle_position_map

def match_angles(angle_position_map, theta, phi):
    # Find closest theta, phi pair to input targets
    diffs = angle_position_map.copy()
    diffs["Theta"] = (diffs["Theta"] - theta).abs()
    diffs["Phi"] = (diffs["Phi"] - phi).abs()
    diffs = diffs.sort_values(["Theta", "Phi"], ascending=True)
    min_index = diffs.index[0]
    row = diffs.ix[min_index]
    # print(row)
    # print(row.keys())
    # print(list(row.keys()))
    # print(row['X'], row['Y'])
    positions_list = ()
    # print(row.keys())
    if 'Interp. X (mm)' in list(row.keys()):
        positions_list += (row['Interp. X (mm)'], row['Interp. Y (mm)'])
    if 'Fitted X Interp. (mm)' in list(row.keys()):
        positions_list += (row['Fitted X Interp. (mm)'], row['Fitted Y Interp. (mm)'])
    if 'X' in list(row.keys()):
        positions_list += (row['X'], row['Y'])
    return positions_list

def table_interpolation(mapping_df, num_interp_points=0, interp_method='linear'):
    # Number of added points inbetween integer angles
    mgrid_dim = complex(0,(num_interp_points+1)*100)

    # X Interpolation
    grid = np.mgrid[-50:50:mgrid_dim, -50:50:mgrid_dim]
    grid_theta_xmap, grid_phi_xmap = grid
    values = mapping_df.X.values
    points = np.vstack((mapping_df.Theta.values, mapping_df.Phi.values)).T
    grid_xmap = griddata(points=points, 
                         values=values, 
                         xi=(grid_theta_xmap, grid_phi_xmap), 
                         method=interp_method)

    # Y Interpolation
    grid = np.mgrid[-50:50:mgrid_dim, -50:50:mgrid_dim]
    grid_theta_ymap, grid_phi_ymap = grid
    values = mapping_df.Y.values
    points = np.vstack((mapping_df.Theta.values, mapping_df.Phi.values)).T
    grid_ymap = griddata(points=points, 
                         values=values, 
                         xi=(grid_theta_ymap, grid_phi_ymap), 
                         method=interp_method)

    # Format x griddata into dataframe
    x_interp_pivot = pd.DataFrame(grid_xmap, 
                                  index=grid_theta_xmap[:,0],
                                  columns=grid_phi_xmap[0,:])
    x_interp_df = x_interp_pivot.unstack().reset_index(name='Interp. X (mm)')
    x_interp_df = x_interp_df.rename(columns={'level_0':'Phi', 'level_1':'Theta'})
    x_interp_df = x_interp_df[['Theta', 'Phi', 'Interp. X (mm)']]

    # Format y griddata into dataframe
    y_interp_pivot = pd.DataFrame(grid_ymap,
                                  index=grid_theta_ymap[:,0],
                                  columns=grid_phi_ymap[0,:])
    y_interp_df = y_interp_pivot.unstack().reset_index(name='Interp. Y (mm)')
    y_interp_df = y_interp_df.rename(columns={'level_0':'Phi', 'level_1':'Theta'})
    y_interp_df = y_interp_df[['Theta', 'Phi', 'Interp. Y (mm)']]

    # Merge the two dataframes into one
    mapping_df = pd.merge(x_interp_df, y_interp_df, on=['Theta', 'Phi'], how='inner')

    return mapping_df

    # ap_map = angle_to_pos_map.copy()
    # x = ap_map['X']
    # y = ap_map['Y']
    # theta = ap_map['Theta']
    # phi = ap_map['Phi']

    # new_theta = [np.linspace(theta.iloc[i], theta.iloc[i + 1], 2 + num_interp_points)
    #              for i in range(len(ap_map) - 1)]
    # new_phi = [np.linspace(phi.iloc[i], phi.iloc[i + 1], 2 + num_interp_points)
    #            for i in range(len(ap_map) - 1)]

    # # X Interpolation
    # x_interp_funcs = [interp2d([theta.iloc[i], theta.iloc[i+1]], 
    #                            [phi.iloc[i], phi.iloc[i+1]], 
    #                            [x.iloc[i], x.iloc[i+1]])
    #                   for i in range(len(ap_map))]
    # x_new_positions = [item[0](item[1], item[2]) for item in zip(x_interp_funcs, 
    #                                                              new_theta,
    #                                                              new_phi)]

    # # Y Interpolation
    # y_interp_funcs = [interp2d([theta.iloc[i], theta.iloc[i+1]],
    #                            [phi.iloc[i], phi.iloc[i+1]], 
    #                            [y.iloc[i], y.iloc[i+1]]) \
    #                   for i in range(len(ap_map))]
    # y_new_positions = [item[0](item[1], item[2]) for item in zip(y_interp_funcs, 
    #                                                              new_theta,
    #                                                              new_phi)]

    # new_theta = np.array(new_theta).flatten()
    # new_phi = np.array(new_phi).flatten()
    # x_new_positions = np.array(x_new_positions).flatten()
    # y_new_positions = np.array(y_new_positions).flatten()

    # # New data frames
    # interp_table = pd.DataFrame()
    # interp_table["Theta"] = new_theta
    # interp_table["Phi"] = new_phi
    # interp_table["X"] = x_new_positions
    # interp_table["Y"] = y_new_positions
    # return interp_table

def add_mapped_interp_points(tracked_angles, mapping_df):
    tracked_angles_sort = tracked_angles.sort_values('Theta Tracking (deg)')
    
    # Merge Mapped Thetas on Tracked Thetas by nearest value
    mapping_df_sort = mapping_df.sort_values('Theta')
    thetas = pd.DataFrame({'Theta' : mapping_df_sort['Theta'], 
                           'Theta Mapping' : mapping_df_sort['Theta']})
    nearest_merge = pd.merge_asof(tracked_angles_sort,
                                  thetas,
                                  left_on='Theta Tracking (deg)', 
                                  right_on='Theta', 
                                  direction='forward')
    nearest_merge['Theta Merge Diff'] = nearest_merge['Theta Tracking (deg)'] - \
                                        nearest_merge['Theta Mapping']
    
    # Merge Mapped Phis on Tracked Phis by nearest value
    mapping_df_sort_half = mapping_df_sort.drop('Theta', axis=1)
    nearest_merge = nearest_merge.sort_values('Phi Tracking (deg)')
    tracked_angles_sort = tracked_angles.sort_values('Phi Tracking (deg)')
    mapping_df_sort_half = mapping_df_sort_half.sort_values('Phi')
    phis = pd.DataFrame({'Phi': mapping_df_sort_half['Phi'], 
                         'Phi Mapping' : mapping_df_sort['Phi']})
    nearest_merge = pd.merge_asof(nearest_merge,
                                  phis,
                                  left_on='Phi Tracking (deg)',
                                  right_on='Phi',
                                  direction='forward')
    nearest_merge['Phi Merge Diff'] = nearest_merge['Phi Tracking (deg)'] - \
                                      nearest_merge['Phi Mapping']

    # Merge the Interpolated Position Data onto the angles
    position_df = pd.merge(nearest_merge.drop(['Theta', 'Phi'], axis=1),
                           mapping_df, 
                           left_on=['Theta Mapping', 'Phi Mapping'],
                           right_on=['Theta','Phi'])
    return position_df

def fit_interp_data(interp_map):
    # _date_str = _date.strftime('%m_%d_%y')
    # tracked_angles = position_df[position_df['Date Local (yyyy-mm-dd)'] == 
    #                  _date.strftime(' %Y-%m-%d')]

    # ax = tracked_angles.plot('Time (hh:mm:ss)', 
    #                          'Interp. X (mm)', 
    #                          grid=True, 
    #                          label='X Position Data for {}'.format(_date_str), 
    #                          figsize=(12,9))
    # tracked_angles.plot('Time (hh:mm:ss)',
    #                     'Interp. Y (mm)', 
    #                     ax=ax, 
    #                     grid=True, 
    #                     label='Y Position Data for {}'.format(_date_str), 
    #                     figsize=(12,9))

    # min_y = interp_map['Interp. Y (mm)'].min()
    # x_init = [5, 1, 5, 1, -1, 1, 1]
    # x_interp = interp_map['Interp. X (mm)']
    # y_interp = interp_map['Interp. Y (mm)']
    # res_lsq = least_squares(sin_cos_plus_resid, x_init, 
    #                         args=(x_interp, y_interp))
    # res_robust = least_squares(sin_cos_plus_resid, x_init, 
    #                            loss='soft_l1', f_scale=.1,
    #                            args=(x_interp, y_interp))
    # y_lsq = par_sin_cos_plus(res_lsq.x, x_interp)
    # y_robust = par_sin_cos_plus(res_robust.x, x_interp)
    
    # interp_map['Fitted Y Interp. (mm)'] = y_robust
    # # interp_map.sort_values(by=['Old Index'], inplace=True)
    # return interp_map

    min_y = interp_map['Interp. Y (mm)'].min()
    # t_init = [5, 1, 5, 1, -1, 1, 1]
    t_init = [0.1, 0.1, 0.1, 0, 0.1, 0.1, 1]
    t_interp = interp_map.index.values
    y_interp = interp_map['Interp. Y (mm)']
    res_lsq = least_squares(sin_cos_plus_resid, t_init, 
                            args=(t_interp, y_interp))
    res_robust = least_squares(sin_cos_plus_resid, t_init, 
                               loss='soft_l1', f_scale=.1,
                               args=(t_interp, y_interp))
    y_lsq = par_sin_cos_plus(res_lsq.x, t_interp)
    y_robust = par_sin_cos_plus(res_robust.x, t_interp)
    
    interp_map['Fitted Y Interp. (mm)'] = y_robust
    # interp_map.sort_values(by=['Old Index'], inplace=True)

    min_x = interp_map['Interp. X (mm)'].min()
    # t_init = [5, 1, 5, 1, -1, 1, 1]
    t_init = [0, 1, 1, 0, 1, 1, 1]
    t_interp = interp_map.index.values
    x_interp = interp_map['Interp. X (mm)']
    res_lsq = least_squares(sin_cos_plus_resid, t_init, 
                            args=(t_interp, x_interp))
    res_robust = least_squares(sin_cos_plus_resid, t_init, 
                               loss='soft_l1', f_scale=.1,
                               args=(t_interp, x_interp))
    x_lsq = par_sin_cos_plus(res_lsq.x, t_interp)
    x_robust = par_sin_cos_plus(res_robust.x, t_interp)
    
    interp_map['Fitted X Interp. (mm)'] = x_robust
    # interp_map.sort_values(by=['Old Index'], inplace=True)
    return interp_map

def get_cos_factors(tilt, azimuth_angles, altitude_angles):
    cos_correct_df = pd.DataFrame()
    # Calculation of cos correction factors
    cos_correct_df['Cos(Theta)'] = altitude_angles.map(math.cos)*azimuth_angles.map(math.sin)
    cos_correct_df['Cos(Phi)'] = (math.sin(tilt)*altitude_angles.map(math.sin) + 
                                  math.cos(tilt)*altitude_angles.map(math.cos)*
                                  azimuth_angles.map(math.cos))
    cos_correct_df['Theta_'] = 90.0 - cos_correct_df['Cos(Theta)'].map(math.acos).map(math.degrees)
    cos_correct_df['Phi_'] = 90.0 - cos_correct_df['Cos(Phi)'].map(math.acos).map(math.degrees)
    cos_correct_df['Cos(Theta)'] = cos_correct_df['Theta_'].map(math.radians).map(math.cos)
    cos_correct_df['Cos(Phi)'] = cos_correct_df['Phi_'].map(math.radians).map(math.cos)
    return cos_correct_df

def get_position_from_angle(data, tilt, num_interp_points=0, interp_method='linear'):
    # Obtain cos factors and corrected data
    azimuth_angles, altitude_angles = data['Azimuth (rad)'], data['Altitude (rad)']
    cos_correct_df = get_cos_factors(tilt, azimuth_angles, altitude_angles)
    # dni_df = self.cos_correct(dni_df, cos_correct_df)

    angles = pd.DataFrame()
    angles['Theta'] = cos_correct_df['Theta_']
    angles['Phi'] = cos_correct_df['Phi_']

    print('Generating the Angle to Position Map...')
    mapping = read_and_clean_map()
    print(mapping.head())
    mapping = table_interpolation(mapping, num_interp_points, interp_method)
    print(mapping.head())
    mapping = fit_interp_data(mapping)
    print(mapping.head())
    mapping = filter_angle_position(mapping)
    print(mapping.head())
    print('Done.')

    def match_angles_wrapper(mapping):
        def match_angles_mapper(angles):
            return match_angles(mapping, angles[0], angles[1])
        return match_angles_mapper

    print('Matching tracked angles to mapped angles...')
    positions = angles.apply(match_angles_wrapper(mapping), axis=1)
    print('Done.')
    print(positions[0])
    positions = [tuple(x[i] for i in range(len(x))) for x in positions]
    print(positions[0])
    positions = zip(*positions)
    print(positions[0])
    positions = pd.DataFrame(positions).transpose()
    print(positions.iloc[0])
    full_position_cols = ['Interp. X (mm)', 
                          'Interp. Y (mm)', 
                          'Fitted X Interp. (mm)',
                          'Fitted Y Interp. (mm)',
                          'X', 'Y']
    col_names = dict(zip(positions.columns, full_position_cols))
    positions = positions.rename(columns=col_names)
    print(positions.iloc[0])
    positions['Datetime Local'] = data['Datetime Local']
    print(positions.iloc[0])
    return positions

def main():
    theta = float(sys.argv[1])
    phi = float(sys.argv[2])
    mapping = filter_angle_position()
    x, y = match_angles(angle_position_map, theta, phi)

def main1():
    print('Starting...')
    mapping = read_and_clean_map()
    # print(len(mapping))
    # print(range(len(mapping) - 1))
    # print(xrange(len(mapping) -1))
    print(mapping)
    mapping_interp = table_interpolation(mapping, num_interp_points=30)
    print(mapping_interp)
    print(len(mapping_interp))



if __name__ == '__main__':
    main1()
