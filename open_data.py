#!/usr/bin/env python
import csv
import numpy as np
from scipy import signal as signal_processing
from copy import deepcopy

from matplotlib.backends import qt4_compat as qt_compat

use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore


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
        self._raw_signal = deepcopy(signal)
        self._signal = deepcopy(signal)

    def _get_elliptic_filter(self, cutoff, order=4, max_ripple=0.01, min_supression=120, padlen=50, btype='lowpass'):
        sample_frequency = 1/(self._t[1] - self._t[0])
        nyquist_frequency = sample_frequency/2
        relative_frequency = cutoff/nyquist_frequency
        return signal_processing.ellip(order, max_ripple, min_supression, relative_frequency, btype=btype)


    def elliptic_filter(self, cutoff, order=4, max_ripple=0.01, min_supression=120, padlen=50, btype='lowpass'):
        b, a = self._get_elliptic_filter(cutoff, order=order, max_ripple=max_ripple, min_supression=min_supression, padlen=padlen, btype=btype)
        self._signal = signal_processing.filtfilt(b, a, self._signal, padlen=padlen)

    def _plot_filter(self, cutoff, order=4, max_ripple=0.01, min_supression=120, padlen=50, btype='lowpass'):
        b, a = self._get_elliptic_filter(cutoff, order=order, max_ripple=max_ripple, min_supression=min_supression, padlen=padlen, btype=btype)
        w,h = signal_processing.freqz(b,a, plot=self._plot_function)

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


class PeakFinder(object):
    def __init__(self, signal, gradient):

        self._time, self._signal = signal.get_xy()
        self._gradient = gradient.get_signal()

        if len(self._time) != len(self._signal) or len(self._time) != len(self._gradient):
            print ("Mismatch of signal lengths")
    def find_peaks(self, threshold):
        found_slope = False
        peaks = []
        for x in range(len(self._time)):
            if found_slope:
                if self._gradient[x] < 0:
                    peaks.append(x)
                    found_slope = False
            else:
                if self._gradient[x] > threshold:
                    found_slope = True
        return peaks

class FilterControl(QtGui.QWidget):
    def __init__(self, default_cutoff, label, filter_type, enabled=True):
        super(FilterControl, self).__init__()
        self.setSizePolicy
        self._filter_type = filter_type
        self._cutoff = default_cutoff
        self._layout = QtGui.QHBoxLayout()
        label = QtGui.QLabel(label)
        label.setAlignment(QtCore.Qt.AlignRight)

        self._layout.addWidget(label)
        self._cutoff_edit_box = QtGui.QLineEdit(str(default_cutoff))
        self._cutoff_edit_box.setFixedWidth(50)
        self._cutoff_edit_box.setAlignment(QtCore.Qt.AlignRight)
        self._layout.addWidget(self._cutoff_edit_box)
        self._layout.addWidget(QtGui.QLabel("Hz"))
        self._enable_box = QtGui.QCheckBox()
        self._enable_box.setChecked(enabled)
        self._layout.addWidget(self._enable_box)
        self.setLayout(self._layout)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum))
        #TODO set validator
