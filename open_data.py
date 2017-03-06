#!/usr/bin/env python
import csv
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

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

class Trace(object):
    def __init__(self, t, signal):
        self._t = t
        self._raw_signal = signal
        self._signal = self._raw_signal

    def _get_elliptic_filter(self, cutoff, order=4, max_ripple=0.01, min_supression=120, padlen=50, btype='lowpass'):
        sample_frequency = 1/(self._t[1] - self._t[0])
        nyquist_frequency = sample_frequency/2
        relative_frequency = cutoff/nyquist_frequency
        return signal.ellip(order, max_ripple, min_supression, relative_frequency, btype=btype)


    def elliptic_filter(self, cutoff, order=4, max_ripple=0.01, min_supression=120, padlen=50, btype='lowpass'):
        b, a = self._get_elliptic_filter(cutoff, order=order, max_ripple=max_ripple, min_supression=min_supression, padlen=padlen, btype=btype)
        self._signal = signal.filtfilt(b, a, self._signal, padlen=padlen)

    def _plot_filter(self, cutoff, order=4, max_ripple=0.01, min_supression=120, padlen=50, btype='lowpass'):
        b, a = self._get_elliptic_filter(cutoff, order=order, max_ripple=max_ripple, min_supression=min_supression, padlen=padlen, btype=btype)
        w,h = signal.freqz(b,a, plot=self._plot_function)

    def _plot_function(self, w, h):
        sample_frequency = 1/(self._t[1] - self._t[0])
        print sample_frequency
        x = w/2/np.pi*sample_frequency  # w in radians/sample. this converts to Hz
        y = abs(h)
        plt.plot(w,h, lw='0.5')
        plt.show()

    def reset_signal(self):
        self._signal = self._raw_signal

    def gradient(self):
        return np.gradient(self._signal)

    def get_signal(self):
        return self._signal

    def normalise(self):
        self._signal = self._signal / np.linalg.norm(self._signal)

    def get_xy(self):
        return self._t, self._signal

    def plot(self, axes, **kwargs):
        self._plot = axes.plot(self._t, self._signal, **kwargs)
        return self._plot

    def __getitem__(self, index):
        return self._signal[index]

    def __len__(self):
        return len(self._signal)
