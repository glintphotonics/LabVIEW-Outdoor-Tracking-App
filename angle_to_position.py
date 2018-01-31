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
from scipy.optimize import curve_fit
from scipy import stats
import sys


def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')


def f(x):
    return math.sqrt(2500 - x**2)


def main():
    theta = float(sys.argv[1])
    phi = float(sys.argv[2])

    df2 = pd.read_csv("../Quad Detector/Reference/Gen1 Angle Position Map.csv", index_col=0)
    # Reference adjustment (Focal Position vs. Solar Angle)
    # Filter out angle pairs that are out of the 50 deg radius
    df2["Theta"] = -df2["Theta"]
    df2["Phi"] = -df2["Phi"]
    # print(df2)
    # print(map(f, df2["Phi"]))
    df2pos = df2[df2["Theta"] >= 0]
    df2neg = df2[df2["Theta"] < 0]
    df3 = df2pos[df2pos["Theta"] <= map(f, df2pos["Phi"])]
    _neghelp = map(f, df2neg["Phi"])
    _neghelp = [-1 * item for item in _neghelp]
    df4 = df2neg[df2neg["Theta"] >= _neghelp]
    ref = pd.concat([df3, df4])
    # print_full(ref)
    df2pos = ref[ref["Phi"] >= 0]
    df2neg = ref[ref["Phi"] < 0]
    df3 = df2pos[df2pos["Phi"] <= map(f, df2pos["Theta"])]
    _neghelp = map(f, df2neg["Theta"])
    _neghelp = [-1 * item for item in _neghelp]
    df4 = df2neg[df2neg["Phi"] >= _neghelp]
    ref = pd.concat([df3, df4])
    print_full(ref)

    diffs = ref.copy()
    diffs["Theta"] = (diffs["Theta"] - theta).abs()
    diffs["Phi"] = (diffs["Phi"] - phi).abs()
    diffs = diffs.sort_values(["Theta", "Phi"], ascending=True)
    # print_full(diffs)
    # print(diffs.index[0])
    min_index = diffs.index[0]
    # print(min_index)
    row = ref.ix[min_index]
    # print(row)
    print(row['X'], row['Y'])

    # ref = 


if __name__ == '__main__':
    main()