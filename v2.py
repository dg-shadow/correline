#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import os
import random

import numpy as np

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

from open_data import *
from controls import *

from scipy import signal

from time import time

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

class MyDoubleCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self,  data, parent, width=5, height=4, dpi=100):
        self._display = Figure(figsize=(width, height), dpi=dpi)
        self._proximal_data_plot = None
        self._distal_data_plot = None
        self._proximal_gradient_plot = None
        self._distal_gradient_plot = None
        self._patch_plots = []

        self.first = True
        FigureCanvas.__init__(self, self._display)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.initialise()

        self._time = data._time

        self._data = data

        self.run()


    def run(self, slp=30, shp=1, dlp=30, dhp=None):
        start = float(time())

        self._proximal_data = Trace(self._data._time, self._data._proximal_data)
        self._distal_data = Trace(self._data._time, self._data._distal_data)

        self._proximal_data.normalise()
        self._distal_data.normalise()

        if slp is not None:
            self._proximal_data.elliptic_filter(slp)
            self._distal_data.elliptic_filter(slp)

        if shp is not None:
            self._proximal_data.elliptic_filter(shp, btype='highpass')
            self._distal_data.elliptic_filter(shp, btype='highpass')

        self._proximal_gradient = Trace(self._data._time, self._proximal_data.gradient())
        self._distal_gradient = Trace(self._data._time, self._distal_data.gradient())

        self._proximal_gradient.normalise()
        self._distal_gradient.normalise()


        if dlp is not None:
            self._proximal_gradient.elliptic_filter(dlp)
            self._distal_gradient.elliptic_filter(dlp)

        if dhp is not None:
            self._proximal_gradient.elliptic_filter(dhp, btype='highpass')
            self._distal_gradient.elliptic_filter(dhp, btype='highpass')

        startp1 = float(time())
        startp2 = float(time())

        self._find_peaks()


        self._proximal = {
            'signal': self._proximal_data,
            'gradient': self._proximal_gradient,
            'peaks': self._proximal_data_peaks
        }

        self._distal = {
            'signal': self._distal_data,
            'gradient': self._distal_gradient,
        }

        self._find_comparison_ranges()

        #print "run %f" % (float(time()) - start)
        start = float(time())
        self._draw()
        self._xmin, self._xmax = self._ax1.get_xlim()
        self._redraw()
        #print "draw %f" % (float(time()) - start)

    def _find_peaks(self):
        self._proximal_data_peaks = PeakFinder(self._proximal_data, self._proximal_gradient).find_peaks(self._peak_find_threshold)

    def _set_peaks(self):
        self._proximal['peaks'] = self._proximal_data_peaks

    def _do_comparison(self):
        xmin, xmax = lower, upper = self._ax1.get_xlim()
        self._draw()
        self._ax1.set_xlim(lower,upper)
        self._ax2.set_xlim(lower,upper)

        self._draw_comparison_ranges()
        # print ("Cross correlating")
        self._do_cross_correlation()
        # print ("Drawing")
        beat = 1


        for patch in self._patch_plots:
            self._remove_plot(patch)
        self._patch_plots = []
        print ("\n\n")
        self._find_num_beats_and_heartrate(self._proximal['peaks'])
        if self._manual_range_setting:
            print ("Comparison ranges set manually (relative to peak in ms): %.2f, %.2f" % (self._manual_range_lower,self._manual_range_upper))
        else:
            print ("Lead in cofficient: %f\nLead out coefficient: %f" % (self._lead_in_coefficient, self._lead_out_coefficient))
        print ("")
        for x, c_range in enumerate(self._proximal['comparison_ranges']):
            if "not_enough_data" in c_range:
                print ("beat %d: Not enough data" % beat)
            else:
                print ("beat: %d, transit time: %f, correlation: %f" % (beat, self._time[c_range['best_fit_mid_point']] - self._time[c_range['mid_point']], c_range['max_correlation']))
                x = self._time[c_range['start_of_range'] + c_range['best_fit_moved_by']:c_range['end_of_range'] + c_range['best_fit_moved_by']]
                y = self._proximal['signal'][c_range['start_of_range']:c_range['end_of_range']]
                self._patch_plots.append(self._ax1.plot(x,y,color='r',lw='0.5'))
            beat  += 1
        self._redraw()


    def _find_comparison_ranges(self):
        ranges = []
        n = 0
        for peak_index in self._proximal['peaks']:
            n += 1
            max_d = 0
            max_d_index = 0
            found_range = False
            current_index = peak_index
            while not found_range:
                current_index -= 1
                if self._proximal['gradient'][current_index] > max_d:
                    max_d = self._proximal['gradient'][current_index]
                    max_d_index = current_index
                elif self._proximal['gradient'][current_index] < 0 and self._time[peak_index] - self._time[current_index] > self._min_t:
                    found_range = True
                    comparison_time_in_samples = max_d_index - current_index


            scaledin = int(float(comparison_time_in_samples) * self._lead_in_coefficient)
            scaledout = int(float(comparison_time_in_samples) * self._lead_out_coefficient)
            #print comparison_time_in_samples

            start_of_range = current_index - scaledin
            end_of_range = current_index + scaledout

            ranges.append({
                'mid_point': current_index,
                'end_of_range': end_of_range,
                'start_of_range': start_of_range,
                't_in_samples': comparison_time_in_samples,
                't_in_seconds': self._time[max_d_index] - self._time[current_index],
                "lead_in_time": self._time
            })
        self._proximal['comparison_ranges'] = ranges

    def _do_cross_correlation(self):
        done = 0
        for comparison_range in self._proximal['comparison_ranges']:
            if "not_enough_data" in comparison_range:
                continue
            # print "starting %d at %d" % (done, comparison_range['mid_point'])
            done += 1
            mid_point = comparison_range['mid_point']
            start_of_range = comparison_range['start_of_range']
            end_of_range = comparison_range['end_of_range']

            if start_of_range < 0 or end_of_range > len(self._distal['signal']):
                start_of_range = 0;
                comparison_range['not_enough_data'] = True
                continue

            range_moved = 0
            max_correlation = None
            max_moved = None

            while end_of_range + range_moved < len(self._proximal['signal']) and self._time[mid_point + range_moved] - self._time[mid_point] < self._max_transit_time:
                moved_start = start_of_range + range_moved
                moved_end = end_of_range + range_moved

                try:
                    diffs = (self._proximal['signal'][start_of_range:end_of_range] - self._distal['signal'][moved_start:moved_end])
                except:
                    print ("Couldn't process beat %d" % done)
                a = self._proximal['signal'][start_of_range:end_of_range]
                v = self._distal['signal'][moved_start:moved_end]

                a = (a - np.mean(a)) / (np.std(a) * len(a))
                v = (v - np.mean(v)) / np.std(v)
                correlation = np.correlate(a,v)[0]
                if max_correlation is None or correlation > max_correlation:
                    max_correlation = correlation
                    max_moved = range_moved

                range_moved += 1
            comparison_range['best_fit_mid_point'] = mid_point + max_moved
            comparison_range['best_fit_moved_by'] = max_moved
            comparison_range['max_correlation'] = max_correlation

    def _set_params(self):
        self._peak_find_threshold = 0.005
        self._t_multiplier = 1.0
        self._min_t = 0.1
        self._max_transit_time = 0.2



    def _draw(self):
        self._ax1.cla()
        self._ax2.cla()

        for plot in [ self._proximal_data_plot, self._distal_data_plot, self._proximal_gradient_plot, self._distal_gradient_plot]:
            if plot is not None:
                self._remove_plot(plot)
        self._proximal_data_plot = self._proximal_data.plot(self._ax1, lw=0.5, color='b')
        self._distal_data_plot = self._distal_data.plot(self._ax1, lw=0.5, color='g')
        self._proximal_gradient_plot = self._proximal_gradient.plot(self._ax2, lw=0.5, color='b')
        self._distal_gradient_plot = self._distal_gradient.plot(self._ax2, lw=0.5, color='g')

        self._ax2.axhline(0, color='k', lw='0.5', ls='dashed')
        self._ax2.axhline(self._peak_find_threshold, color='k', lw='0.5', ls='dashed')

        self._draw_peaks(self._proximal_data_peaks, self._proximal_data_peak_plots,'b')


        self._draw_roi_bounds()

        self._draw_comparison_ranges()

        self._ax1.autoscale(axis='y')
        self._ax2.autoscale(axis='y')

    def _find_num_beats_and_heartrate(self, peaks):
        num_peaks = len(peaks)
        num_beats = num_peaks - 1
        start_time = self._time[peaks[0]]
        end_time = self._time[peaks[-1]]
        heart_rate = (end_time - start_time) / num_beats * 60
        print ("Number of peaks: %d\nNumber of beats: %d\nHeart rate: %.2fbpm" % (num_peaks, num_beats, heart_rate))

    def _draw_comparison_ranges(self):
        for plot in (self._range_limit_plots):
            self._remove_line(plot)
        self._range_limit_plots[:] = []

        for c_range in self._proximal['comparison_ranges']:
            if "not_enough_data" in c_range:
                continue
            self._range_limit_plots.append(self._ax1.axvline(self._time[c_range["start_of_range"]], color="r", lw='0.3', ls='dashed'))
            self._range_limit_plots.append(self._ax1.axvline(self._time[c_range["end_of_range"]], color="y", lw='0.3', ls='dashed'))
        self._redraw()

    def _draw_peaks(self, peaks, plots, color):
        for plot in plots:
            self._remove_line(plot)
        plots[:] = []
        for x in peaks:
            plots.append(self._ax1.axvline(self._time[x], color=color, lw='0.5', ls='dashed'))

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
        return
        line = plot.pop(0)
        self._remove_line(line)

    def _remove_line(self, line):
        try:
            line.remove()
            del line
        except Exception:
            pass


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
        self._proximal_data_peak_plots = []
        self._distal_data_peak_plots = []
        self._range_limit_plots = []

        self._display.canvas.mpl_connect("scroll_event", self._scroll_event)
        self._lead_in_coefficient = 1.0
        self._lead_out_coefficient = 1.0
        self._manual_range_setting = False

    def _scroll_event(self, event):
        # print (event.key)
        # print (event.step)
        # print (type(event))
        if event.key is None:
            self._scroll(event)
        elif event.key == "control":
            self._zoom(event)

    def _zoom(self, event):
        lower, upper = self._ax1.get_xlim()

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

        # print ("Entering %s mode." % str(mode))

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
    def __init__(self, input_file, proximal_col, distal_col, inverted, start_line):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.main_widget = QtGui.QWidget(self)

        self.layout = QtGui.QHBoxLayout(self.main_widget)

        self._data = OpenData(input_file, proximal_col, distal_col, inverted, start_line)

        self._graph = MyDoubleCanvas(self._data, self.main_widget, width=5, height=4, dpi=100)

        self._set_up_controls()
        self._connect_signals()
        self._run_with_filters()

        self.layout.addWidget(self._graph)
        self.layout.addWidget(self._controls_widget)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def _run_with_filters(self, event=None):
        self._graph.run(
            self._s_lp_filter.get_cutoff(),
            self._s_hp_filter.get_cutoff(),
            self._d_lp_filter.get_cutoff(),
            self._d_hp_filter.get_cutoff()
        )

    def _manual_range_enable(self, enable):
        self._lead_in_edit.setEnabled(not enable)
        self._lead_out_edit.setEnabled(not enable)
        self._graph._manual_range_setting = enable
        if not enable:
            self._graph._find_comparison_ranges()
            self._graph._draw_comparison_ranges()
        self._graph._draw()

    def _manual_range_set(self, upper, lower):
        self._manual_range_upper = upper/1000
        self._manual_range_lower = lower/1000
        self._graph._manual_range_upper = upper
        self._graph._manual_range_lower = lower
        self._set_manual_ranges()
        self._graph._draw_comparison_ranges()

    def _set_manual_ranges(self):
        ranges = []
        sample_interval = self._data.get_sample_interval()
        lower_interval = int(self._manual_range_lower/sample_interval)
        upper_interval = int(self._manual_range_upper/sample_interval)
        mid_point_interval = int((lower_interval + upper_interval) /2)
        beat = 1
        for peak in self._graph._proximal['peaks']:
            end_of_range = peak + upper_interval
            start_of_range = peak + lower_interval
            if (end_of_range > len(self._graph._distal['signal']) or start_of_range < 0):
                comparison_range = {"not_enough_data" : True}
                print ("Not enough data for beat %d" % beat)
            else:
                comparison_range = {
                    'mid_point': peak + mid_point_interval,
                    'end_of_range': end_of_range,
                    'start_of_range': start_of_range
                    }
            ranges.append(comparison_range)
            beat += 1
                # 't_in_samples': 0comparison_time_in_samples,
                # 't_in_seconds': self._time[max_d_index] - self._time[current_index],
                # "lead_in_time": self._time
        self._graph._proximal["comparison_ranges"] = ranges


    def _set_peak_threshold(self, value):
        self._graph._peak_find_threshold = value
        self._graph._find_peaks()
        self._graph._set_peaks()
        self._graph._draw()
        self._graph._redraw()

    def _set_up_controls(self):
        self._controls_widget = QtGui.QWidget()
        self._controls_widget.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum))
        self._controls_layout = QtGui.QVBoxLayout()
        self._controls_widget.setLayout(self._controls_layout)
        self._roi_mode_button = QtGui.QPushButton("Set ROI")
        self._controls_layout.addWidget(self._roi_mode_button)

        self._roi_zoom_button = QtGui.QPushButton("Zoom to ROI")
        self._controls_layout.addWidget(self._roi_zoom_button)

        self._zoom_out_button = QtGui.QPushButton("Zoom Out")
        self._controls_layout.addWidget(self._zoom_out_button)

        self._beat_threshold_controller = DoubleEdit(0.005, "Peak Finder Threshold", self._set_peak_threshold)
        self._controls_layout.addWidget(self._beat_threshold_controller)

        self._lead_in_edit = DoubleEdit(1.0, "Lead In:  ", self._set_lead_in)
        self._lead_out_edit = DoubleEdit(1.0, "Lead Out:", self._set_lead_out)
        self._comparison_range_control  = ComparisonRangeSetter(-30, -200, self._manual_range_enable, self._manual_range_set, False)

        self._controls_layout.addWidget(self._comparison_range_control)
        self._controls_layout.addWidget(self._lead_in_edit)
        self._controls_layout.addWidget(self._lead_out_edit)


        self._do_comparison_button = QtGui.QPushButton("Run Comparison")
        self._controls_layout.addWidget(self._do_comparison_button)

        self._s_lp_filter = FilterControl(30, "Signal LP  ", "lpass")
        self._s_hp_filter = FilterControl(1,  "Signal HP  ", "hpass")
        self._d_lp_filter = FilterControl(30, "Gradient LP", "lpass")
        self._d_hp_filter = FilterControl(1,  "Gradient HP", "hpass", enabled=False)


        self._controls_layout.addWidget(self._s_lp_filter)
        self._controls_layout.addWidget(self._s_hp_filter)
        self._controls_layout.addWidget(self._d_lp_filter)
        self._controls_layout.addWidget(self._d_hp_filter)

        self._controls_layout.addWidget(QtGui.QWidget())

    def _set_lead_in(self, value):
        self._graph._lead_in_coefficient = float(value)
        self._graph._find_comparison_ranges()
        self._graph._draw_comparison_ranges()

    def _set_lead_out(self, value):
        self._graph._lead_out_coefficient = float(value)
        self._graph._find_comparison_ranges()
        self._graph._draw_comparison_ranges()

    def _connect_signals(self):
        self._roi_mode_button.clicked.connect(self._graph._roi_mode_button)
        self._roi_zoom_button.clicked.connect(self._graph._zoom_to_roi)
        self._zoom_out_button.clicked.connect(self._graph._zoom_out)
        self._do_comparison_button.clicked.connect(self._graph._do_comparison)
        self._d_lp_filter.connect(self._run_with_filters)
        self._d_hp_filter.connect(self._run_with_filters)
        self._s_lp_filter.connect(self._run_with_filters)
        self._s_hp_filter.connect(self._run_with_filters)

import getopt

try:
    opts, args = getopt.getopt(sys.argv[1:],'id:p:f:s:')
except getopt.GetoptError:
      print 'Usage: v2.py -p proximal_col -d distal_col -f filename -s start_line [-i (inverted)]'
      exit(2)

proximal_col = 1
distal_col = 2
inverted = False
input_file = 'input.txt'
start_line = 0
for opt, arg in opts:
    if opt == '-p':
        proximal_col = int(arg)
    elif opt == '-d':
        distal_col = int(arg)
    elif opt == '-s':
        start_line = int(arg)
    elif opt == '-i':
        inverted = True
    elif opt == '-f':
        input_file = arg

print ("Input file: %s\nProximal column: %d\nDistal column: %d\nData inverted: %r\nData starts: Line %d" % (
    input_file, proximal_col, distal_col, inverted, start_line))


qApp = QtGui.QApplication(sys.argv)
aw = ApplicationWindow(input_file, proximal_col, distal_col, inverted, start_line)
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())
