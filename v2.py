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

from scipy import signal

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
        self._xmin, self._xmax = self._ax1.get_xlim()

    def _lpf(self, x, cutoff):
        sample_frequency = 1/(self._data._time[1] - self._data._time[0])
        nyq = sample_frequency/2
        relative = cutoff/nyq
        b, a = signal.ellip(4, 0.01, 120, relative) 
        return signal.filtfilt(b, a, x, padlen=50)

    def _draw(self):
        self._s1plot = self._ax1.plot(self._data._time, self._data._s1, lw=0.5)
        self._s2plot = self._ax1.plot(self._data._time, self._data._s2, lw=0.5)
        self._d1plot = self._ax2.plot(self._data._time, self._lpf(self._data._d1, 30), lw=.5)
        self._d2plot = self._ax2.plot(self._data._time, self._lpf(self._data._d2, 30), lw=.5)
    
        self._ax2.axhline(0, color='k', lw='0.5', ls='dashed')
        self._draw_roi_bounds()

    def _draw_roi_bounds(self):
        if self._roi_upper_bound_line is not None:
            self._remove_line(self._roi_upper_bound_line[0])
            self._remove_line(self._roi_upper_bound_line[1])
            self._roi_upper_bound_line = None
        if self._roi_upper_bound is not None:
            self._roi_upper_bound_line = []
            self._roi_upper_bound_line.append(self._ax1.axvline(self._roi_upper_bound, color="b"))
            self._roi_upper_bound_line.append(self._ax2.axvline(self._roi_upper_bound, color="b"))
        if self._roi_lower_bound_line is not None:
            self._remove_line(self._roi_lower_bound_line[0])
            self._remove_line(self._roi_lower_bound_line[1])
            self._roi_lower_bound_line = None
        if self._roi_lower_bound is not None:
            self._roi_lower_bound_line = []
            self._roi_lower_bound_line.append(self._ax1.axvline(self._roi_lower_bound, color="r"))
            self._roi_lower_bound_line.append(self._ax2.axvline(self._roi_lower_bound, color="r"))

    def _remove_plot(self, plot):
        line = plot.pop(0)
        self._remove_line(line)

    def _remove_line(self, line):
        line.remove()
        del line

    def initialise(self):
        self._ax1 = self._display.add_subplot(211)
        self._ax2 = self._display.add_subplot(212)

        self._roi_upper_bound = None  # roi = region of interest.
        self._roi_lower_bound = None
        self._roi_upper_bound_line = None
        self._roi_lower_bound_line = None

        self._mode = None
        self._enter_mode_functions = {}
        self._leave_mode_functions = {}
        self._enter_mode_functions["select_roi"] = self._enter_roi_mode
        self._leave_mode_functions["select_roi"] = self._leave_roi_mode

        self._display.canvas.mpl_connect("scroll_event", self._scroll_event)

    def _scroll_event(self, event):
        print (event.key)
        print (event.step)
        if event.key is None:
            self._scroll(event)
        elif event.key == "control":
            self._zoom(event)

    def _zoom(self, event):
        lower, upper = self._ax1.get_xlim()

        print ("zooming")

        window = upper - lower
        change = window/50

        upper_fraction = change * (upper - event.xdata) / window
        lower_fraction = change - lower_fraction

        if event.button == "up":
           new_upper = upper - change
           new_lower = lower + change
        elif event.button == "down":
           new_upper = upper + change
           new_lower = lower - change

        if new_upper >  self._xmax or new_lower < self._data._time[0]:
            return

        self._ax1.set_xlim([new_lower, new_upper])
        self._ax2.set_xlim([new_lower, new_upper])
        self._redraw()


    def _scroll(self, event):
        lower, upper = self._ax1.get_xlim()
        window = upper - lower

        change = window/50 * event.step

        new_upper = upper + change
        new_lower = lower + change

        if event.button == "up":
            if upper > self._xmax:
                return
            new_upper = upper + window/50 * event.step
            if new_upper > self._xmax:
                new_upper = self._xmax
            if new_upper < upper:
                new_upper = upper
            change = new_upper - upper
            new_lower = lower + change
        elif event.button == "down":
            if lower < self._xmin:
                return
            new_lower = lower + window/50 * event.step
            if new_lower < self._xmin:
                new_lower = self._xmin
            if new_lower > lower:
                new_lower = lower
            change = lower - new_lower
            new_upper = upper - change

        self._ax1.set_xlim([new_lower, new_upper])
        self._ax2.set_xlim([new_lower, new_upper])
        self._redraw()
        

    def _enter_mode(self, mode):
        if self._mode == mode:
            return

        print ("Entering %s mode." % str(mode))
        
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
        self._roi_cursor = ClickCursor(self._set_roi_limit, self._display.canvas, (self._ax1, self._ax2),
                                       useblit=True, color='k')
        self._redraw()

    def _set_roi_limit(self, event):
        if event.button == 1:
            self._roi_lower_bound = event.xdata
        else:
            self._roi_upper_bound = event.xdata

        if self._roi_lower_bound is not None and self._roi_upper_bound is not None \
           and self._roi_lower_bound > self._roi_upper_bound:

            lower = self._roi_upper_bound
            self._roi_upper_bound = self._roi_lower_bound
            self._roi_lower_bound = lower

        self._draw_roi_bounds()
        self._redraw()

    def _leave_roi_mode(self):
        del(self._roi_cursor)
        self._redraw()

    def _redraw(self):
        FigureCanvas.draw(self)        

    def _zoom_to_roi(self):
        if self._roi_upper_bound is None or self._roi_lower_bound is None:
            return
        window = self._roi_upper_bound - self._roi_lower_bound
        upper = self._roi_upper_bound + window/15
        lower = self._roi_lower_bound - window/15
        
        self._ax1.set_xlim([lower, upper])
        self._ax2.set_xlim([lower, upper])

        self._redraw()

    def _zoom_out(self):
        self._ax1.autoscale()
        self._ax2.autoscale()
        self._redraw()

class ClickCursor(MultiCursor):
    def __init__(self, function, *args, **kwargs):
        MultiCursor.__init__(self, *args, **kwargs)
        self._cid = self.canvas.mpl_connect("button_press_event", function)

    def __del__(self):
        self.canvas.mpl_disconnect(self._cid)

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

        self._roi_zoom_button = QtGui.QPushButton("Zoom to ROI")
        self._controls_layout.addWidget(self._roi_zoom_button)

        self._zoom_out_button = QtGui.QPushButton("Zoom Out")
        self._controls_layout.addWidget(self._zoom_out_button)

        self._controls_layout.addWidget(QtGui.QWidget())


    def _connect_signals(self):
        self._roi_mode_button.clicked.connect(self._graph._roi_mode_button)
        self._roi_zoom_button.clicked.connect(self._graph._zoom_to_roi)
        self._zoom_out_button.clicked.connect(self._graph._zoom_out)


qApp = QtGui.QApplication(sys.argv)

aw = ApplicationWindow()
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())
#qApp.exec_()
