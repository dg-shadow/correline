from __future__ import unicode_literals
import sys
import os
import random
from matplotlib.backends import qt4_compat as qt_compat
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE


if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore

from numpy import arange, sin, pi
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import open_data


progname = os.path.basename(sys.argv[0])
progversion = "0.1"

class MyDoubleCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, data, parent, width=5, height=4, dpi=100):
        self._display = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, self._display)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


        self._ax1 = self._display.add_subplot(211)
        self._ax2 = self._display.add_subplot(212, sharex=self._ax1)
        self._data = data

        self.compute_initial_figure()

    def compute_initial_figure(self):
        self._ax1.cla()
        self._ax2.cla()
        self.s1plot = self._ax1.plot(self._data._time, self._data._s1)
        self.s2plot = self._ax1.plot(self._data._time, self._data._s2)
        self.d1plot = self._ax2.plot(self._data._time, self._data._d1)
        self.d2plot = self._ax2.plot(self._data._time, self._data._d2)

    def initialise(self):
        self._mode = None
        self._roi_upper_bound = None  # roi = region of interest.
        self._roi_lower_bound = None

    def set_mode(self, mode):
        if mode == "select_roi":
            self._mode = mode
        elif mode is None:
            self._mode = None
        else:
            print "Incorrect mode selected!"

class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QtGui.QWidget(self)

        l = QtGui.QVBoxLayout(self.main_widget)

        self.data = open_data.OpenData("./processed.csv")
        self.graph = MyDoubleCanvas(self.data, self.main_widget, width=5, height=4, dpi=100)
        l.addWidget(self.graph)
        
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

qApp = QtGui.QApplication(sys.argv)

aw = ApplicationWindow()
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())
#qApp.exec_()
