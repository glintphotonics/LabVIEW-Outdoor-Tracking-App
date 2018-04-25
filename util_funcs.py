# Calibration for quad photodiode using .txt file that specifies theta, phi, y sensor, x sensor, y 
# sensor variance, and x sensor variance (in that order). The .txt file is an output from LabVIEW.

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


def arccos_resid(x, t, y):
    return x[0]*np.arccos(x[1] * t) + x[2] - y

def arcsin_resid(x, t, y):
    return x[0]*np.arcsin(x[1] * t) + x[2] - y

def sin_resid(x, t, y):
    return x[0]*np.sin(x[1] * t) + x[2] - y

def cos_resid(x, t, y):
    return x[0]*np.cos(x[1] * t) + x[2] - y

def cos_arcsin_resid(x, t, y):
    return x[0]*np.cos(x[1] * t)*np.arcsin(t) + x[2] - y

def fifth_deg_resid(x, t, y):
    return x[0]*t**5 + x[1]*t**4 + x[2]*t**3 + x[3]*t**2 + x[4]*t - y

def third_deg_resid(x, t, y):
    return x[0]*t**3 + x[2]*t + x[3] - y

def sin_cos_resid(x,t,y):
    y_pred = x[0]*(np.sin(x[1]*t + x[2])+0j)*(np.cos(x[3]*t + x[4])+0j) + x[5]
    result = y_pred - y
    return result.real

def sin_cos_plus_resid(x, t, y):
    y_pred = x[0]*(np.sin(x[1] * t + x[2])+0j) + x[3]*(np.cos(x[4]*t + x[5])+0j) + x[6]
    result = y_pred - y
    return result.real

def sigmoid_resid(x, t, y):
    y_pred = x[0]/(x[1] + np.exp(x[2] * t + x[3]))
    result = y_pred - y
    return result.real

def linear_resid(x, t, y):
    return x[0] * t + x[1] - y

def par_arcsin(x, t):
    return x[0]*np.arcsin(x[1] * t) + x[2]

def par_arccos(x, t):
    return x[0]*np.arccos(x[1] * t) + x[2]

def par_sin(x, t):
    return x[0]*np.sin(x[1] * t) + x[2]

def par_cos(x, t):
    return x[0]*np.cos(x[1] * t) + x[2]

def par_cos_arcsin(x, t):
    return x[0]*np.cos(x[1] * t)*np.arcsin(t) + x[2]

def par_fifth_deg(x, t):
    return x[0]*t**5 + x[1]*t**4 + x[2]*t**3 + x[3]*t**2 + x[4]*t

def par_third_deg(x, t):
    return x[0]*t**3 + x[2]*t +x[3]

def par_sin_cos(x, t):
    y_pred = x[0]*np.sin(x[1]*t + x[2])*np.cos(x[3]*t + x[4]) + x[5]
    result = y_pred
    return result.real

def par_sin_cos_plus(x, t):
    y_pred = x[0]*(np.sin(x[1] * t + x[2])) + x[3]*(np.cos(x[4]*t + x[5])) + x[6]
    result = y_pred
    return result.real

def par_sigmoid(x, t):
    y_pred = x[0]/(x[1] + np.exp(x[2] * t + x[3]))
    result = y_pred
    return result.real

def par_linear(x, t):
    return x[0] * t + x[1]

def darccos_dt(x, s, ds_dt):
    return -ds_dt * x[0] * x[1] / np.sqrt(1 - (x[1] * s)**2)

def darcsin_dt(x, s, ds_dt):
    return ds_dt * x[0] * x[1] / np.sqrt(1 - (x[1] * s)**2)

def dsin_cos_plus_dt(x, s, ds_dt):
    return ds_dt * x[0]*x[1]*np.cos(x[1]*s + x[2]) - ds_dt * x[3]*x[4]*np.sin(x[4]*s + x[5])

def dsin_cos_dt(x, s, ds_dt):
    cos_cos = np.cos(x[1]*s + x[2]) * np.cos(x[3]*s + x[4])
    sin_sin = np.sin(x[1]*s + x[2]) * np.sin(x[3]*s + x[4])
    return ds_dt * x[0] *(x[1] * cos_cos - x[3] * sin_sin)