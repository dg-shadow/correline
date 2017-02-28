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
from matplotlib.widgets import MultiCursor

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


        self._data = data

        self.initialise()
        self._draw()

    def _draw(self):
        self.s1plot = self._ax1.plot(self._data._time, self._data._s1)
        self.s2plot = self._ax1.plot(self._data._time, self._data._s2)
        self.d1plot = self._ax2.plot(self._data._time, self._data._d1)
        self.d2plot = self._ax2.plot(self._data._time, self._data._d2)

    def initialise(self):
        self._ax1 = self._display.add_subplot(211)
        self._ax2 = self._display.add_subplot(212)

        self._roi_upper_bound = None  # roi = region of interest.
        self._roi_lower_bound = None

        self._mode = None
        self._enter_mode_functions = {}
        self._leave_mode_functions = {}
        self._enter_mode_functions["select_roi"] = self._enter_roi_mode
        self._leave_mode_functions["select_roi"] = self._leave_roi_mode

    def _enter_mode(self, mode):
        if self._mode == mode:
            return

        print "Entering %s mode." % str(mode)
        
        if self._mode is not None:
            self._leave_mode()

        if mode is None:
            return

        self._enter_mode_functions[mode]()
        self._mode = mode

    def _leave_mode(self):
        self._leave_mode_functions[self._mode]()
        self._mode = None

    def _roi_mode_button(self):
        if self._mode == "select_roi":
            self._enter_mode(None)
        else:
            self._enter_mode("select_roi")

    def _enter_roi_mode(self):
        self._roi_cursor = MultiCursor(self._display.canvas, (self._ax1, self._ax2), useblit=True, color='k')
        self._redraw()

    def _leave_roi_mode(self):
        del(self._roi_cursor)
        self._redraw()

    def _redraw(self):
        FigureCanvas.draw(self)        


class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QtGui.QWidget(self)

        self.layout = QtGui.QHBoxLayout(self.main_widget)

        self._data = open_data.OpenData("./processed.csv")
        self._graph = MyDoubleCanvas(self._data, self.main_widget, width=5, height=4, dpi=100)

        self._set_up_controls()
        self._connect_signals()

        self.layout.addWidget(self._graph)
        self.layout.addWidget(self._controls_widget)
        
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def _set_up_controls(self):
        self._controls_widget = QtGui.QWidget()
        self._controls_layout = QtGui.QVBoxLayout()
        self._controls_widget.setLayout(self._controls_layout)

        self._roi_mode_button = QtGui.QPushButton("Set ROI")
        self._controls_layout.addWidget(self._roi_mode_button)
        self._controls_layout.addWidget(QtGui.QWidget())
    def _connect_signals(self):
        self._roi_mode_button.clicked.connect(self._graph._roi_mode_button)

qApp = QtGui.QApplication(sys.argv)

aw = ApplicationWindow()
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())
#qApp.exec_()
