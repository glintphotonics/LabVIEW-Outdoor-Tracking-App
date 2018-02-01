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
from  Tkinter import *
import Tkinter, Tkconstants, tkFileDialog


def print_full(x):
    pd.set_option('display.max_rows', len(x))
    print(x)
    pd.reset_option('display.max_rows')


def f(x):
    return math.sqrt(2500 - x**2)


def main():
    Tk().withdraw()
    file = tkFileDialog.askopenfilename()
    print (file)

    df2 = pd.read_csv(file, index_col=0)
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
    # print_full(ref)

    fig = plt.figure()
    ax = fig.gca()
    # ax.set_xticks(numpy.arange(0, 1, 0.1))
    # ax.set_yticks(numpy.arange(0, 1., 0.1))
    major_x_ticks = np.arange(min(ref['X']), max(ref['X']), 1)
    minor_x_ticks = np.arange(min(ref['X']), max(ref['X']), 0.2)
    major_y_ticks = np.arange(min(ref['Y']), max(ref['Y']), 1)
    minor_y_ticks = np.arange(min(ref['Y']), max(ref['Y']), 0.2)
    ax.set_xticks(major_x_ticks)
    ax.set_xticks(minor_x_ticks, minor=True)
    ax.set_yticks(major_y_ticks)
    ax.set_yticks(minor_y_ticks, minor=True)
    ax.grid(color='black')
    plt.scatter(ref['X'], ref['Y'], s=2)
    plt.show()


if __name__ == '__main__':
    main()