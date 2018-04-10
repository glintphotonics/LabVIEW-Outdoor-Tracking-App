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


def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')

def f(x):
    return math.sqrt(2500 - x**2)

def read_and_clean_angle_position():
    angleposition = pd.read_csv("../../Quad Detector/Reference/Gen1 1deg Angle Position Map.csv", 
                                index_col=0)
    # Reference adjustment (Focal Position vs. Solar Angle)
    # Filter out angle pairs that are out of the 50 deg radius
    # Flip axes of reference file (To make positive posisitions matchup with positive angles)
    angleposition["Theta"] = -angleposition["Theta"]
    angleposition["Phi"] = -angleposition["Phi"]

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
    row = angle_position_map.ix[min_index]
    # print(row)
    # print(row['X'], row['Y'])
    return row['X'], row['Y']

def main():
    theta = float(sys.argv[1])
    phi = float(sys.argv[2])
    mapping = read_and_clean_angle_position()
    x, y = match_angles(angle_position_map, theta, phi)


if __name__ == '__main__':
    main()
