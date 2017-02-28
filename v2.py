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
        self._ax1 = self._display.add_subplot(211)
        self._ax2 = self._display.add_subplot(212)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, self._display)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

# class DoubleCanvas(FigureCanvas):
#     """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

#     def __init__(self, data, parent=None, width=5, height=4, dpi=100):
        
#         self._display = Figure(figsize=(width, height), dpi=dpi)
#         self.ax1 = self.display.add_subplot(211)
#         self.ax2 = self.display.add_subplot(212)

#         self.time = data._time
#         self.s1 = data._s1
#         self.s2 = data._s2
#         self.d1 = data._d1
#         self.d2 = data._d2

#         self.plot()


#         self.setParent(parent)

#         FigureCanvas.setSizePolicy(self,
#                                    QtGui.QSizePolicy.Expanding,
#                                    QtGui.QSizePolicy.Expanding)
#         FigureCanvas.updateGeometry(self)


#     def plot(self):
#         self.ax1.cla()
#         self.ax2.cla()
#         self.s1plot = self.ax1.plot(self.time, self.s1)
#         self.s2plot = self.ax1.plot(self.time, self.s2)
#         self.d1plot = self.ax2.plot(self.time, self.d1)
#         self.d2plot = self.ax2.plot(self.time, self.d2)

#     def remove_plot(self, plot):
#         line = plot.pop(0)
#         line.remove()
#         del line

class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QtGui.QWidget(self)

        l = QtGui.QVBoxLayout(self.main_widget)

        self.data = open_data.OpenData("./processed.csv")
        # self.graph = DoubleCanvas(self.data, parent=self.main_widget, width=5, height=4, dpi=100)
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
