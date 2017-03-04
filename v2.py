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

class PeakFinder(object):
    def __init__(self, signal, gradient):

        self._time, self._signal = signal.get_xy()
        self._gradient = gradient.get_signal()

        if len(self._time) != len(self._signal) or len(self._time) != len(self._gradient):
            print "Mismatch of signal lengths"

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

        self.initialise()

        self._s1 = open_data.Trace(data._time, data._s1)
        self._s2 = open_data.Trace(data._time, data._s2)
        self._d1 = open_data.Trace(data._time, self._s1.gradient())
        self._d2 = open_data.Trace(data._time, self._s2.gradient())

        self._time = data._time

        self._s1.normalise()
        self._s2.normalise()
        self._d1.normalise()
        self._d2.normalise()

        self._d1.eliptic_filter(30)
        self._d2.eliptic_filter(30)

        self._s1_peaks = PeakFinder(self._s1, self._d1).find_peaks(self._peak_find_threshold)
        self._s2_peaks = PeakFinder(self._s2, self._d2).find_peaks(self._peak_find_threshold)

        self._proximal = {
            'signal': self._s2,
            'gradient': self._d2,
            'peaks': self._s2_peaks
        }

        self._distal = {
            'signal': self._s1,
            'gradient': self._d1,
            'peaks': self._s1_peaks
        }

        print "finding ranges"
        self._proximal['comparison_ranges'] = self._find_comparison_ranges(self._proximal)
        print "cross correlating"
        self._do_cross_correlation()
        print "drawing"

        val = 1
        for x in self._proximal['comparison_ranges']:
            print "transit time %d = %f" % (val, self._time[x['best_fit_mid_point']] - self._time[x['mid_point']])
            val += 1

        self._draw()
        self._xmin, self._xmax = self._ax1.get_xlim()

    def _find_comparison_ranges(self, signal):
        ranges = []
        for peak_index in signal['peaks']:
            max_d = 0
            max_d_index = 0
            found_range = False
            current_index = peak_index
            while not found_range:
                current_index -= 1
                if signal['gradient'][current_index] > max_d:
                    max_d = signal['gradient'][current_index]
                elif signal['gradient'][current_index] < 0 and self._time[peak_index] - self._time[current_index] > self._min_t:
                    found_range = True
            ranges.append({
                'mid_point': current_index,
                't_in_samples': peak_index - current_index,
                't_in_seconds': self._time[peak_index] - self._time[current_index]
            })
        return ranges

    def _do_cross_correlation(self):
        done = 1
        for comparison_range in self._proximal['comparison_ranges']:
            # print "starting %d at %d" % (done, comparison_range['mid_point'])
            done += 1
            mid_point = comparison_range['mid_point']
            start_of_range = mid_point - comparison_range['t_in_samples']
            end_of_range = mid_point + comparison_range['t_in_samples']
            range_moved = 0
            min_squared_differences = None
            min_moved = None

            while end_of_range + range_moved < len(self._proximal['signal']) and self._time[mid_point + range_moved] - self._time[mid_point] < self._max_transit_time:
                start = start_of_range + range_moved
                end = end_of_range + range_moved
                diffs = (self._proximal['signal'][start_of_range:end_of_range] - self._distal['signal'][start:end])
                squared_differences = diffs**2
                summed_squared_differences = squared_differences.sum()
                # for x in range(start_of_range + range_moved, end_of_range + range_moved, 1):
                #     squared_differences += (self._proximal['signal'][x] - self._distal['signal'][x])**2
                if min_squared_differences is None or summed_squared_differences < min_squared_differences:
                    min_squared_differences = summed_squared_differences
                    min_moved = range_moved
                range_moved += 1
            # print "tested range up to %d. min at %d" % (range_moved, min_moved)
            comparison_range['best_fit_mid_point'] = mid_point + min_moved
            comparison_range['best_fit_moved_by'] = min_moved

    def _set_params(self):
        self._peak_find_threshold = 0.5
        self._t_multiplier = 1.0
        self._min_t = 0.01
        self._max_transit_time = 0.2

    def _draw(self):
        self._s1plot = self._s1.plot(self._ax1, lw=0.5)
        self._s2plot = self._s2.plot(self._ax1, lw=0.5)
        self._d1plot = self._d1.plot(self._ax2, lw=0.5)
        self._d2plot = self._d2.plot(self._ax2, lw=0.5)
        
        self._ax2.axhline(0, color='k', lw='0.5', ls='dashed')
        self._ax2.axhline(0.5, color='k', lw='0.5', ls='dashed')

        self._draw_peaks(self._s1_peaks,'b')
        self._draw_peaks(self._s2_peaks, 'g')

        self._draw_roi_bounds()

    def _draw_peaks(self, peaks, color):
        for x in peaks:
            self._ax1.axvline(self._time[x], color=color, lw='0.5', ls='dashed')

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

        self._set_params()

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
        # print (event.key)
        # print (event.step)
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

        if new_upper >  self._xmax or new_lower < self._xmin:
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
