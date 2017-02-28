#!/usr/bin/env python
import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from pylab import figure, show, np

class OpenData(object):
    def __init__(self,  path):
        self._time = []
        self._s1 = []
        self._s2 = []
        self._d1 = []
        self._d2 = []

        with open(path) as f:
            reader = csv.reader(f, delimiter=",")
            d = list(reader)
        for x in range(len(d)):
                self._time.append(float(d[x][0]))
                self._s1.append(float(d[x][1]))
                self._s2.append(float(d[x][2]))
                self._d1.append(float(d[x][3]))
                self._d2.append(float(d[x][4]))


        self._s1 = self._s1 / np.linalg.norm(self._s1)
        self._s2 = self._s2 / np.linalg.norm(self._s2)
        self._d1 = self._d1 / np.linalg.norm(self._d1)
        self._d2 = self._d2 / np.linalg.norm(self._d2)


