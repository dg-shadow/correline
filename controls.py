import matplotlib
matplotlib.use("Qt4Agg")
from matplotlib.backends import qt_compat
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore


class ComparisonRangeSetter(QtGui.QWidget):
    def __init__(self, default_upper, default_lower, enable_callback, edit_callback, enabled=False):
        super(ComparisonRangeSetter, self).__init__()
        self._layout = QtGui.QVBoxLayout()
        self._enable_checkbox = QtGui.QCheckBox("Manual range selection")
        self._enable_checkbox.setChecked(enabled)
        self._layout.addWidget(self._enable_checkbox)
        self._upper_edit = DoubleEdit(default_upper, "Upper Bound (ms)", self._bounds_changed)
        self._lower_edit = DoubleEdit(default_lower, "Lower Bound (ms)", self._bounds_changed)
        self._layout.addWidget(self._upper_edit)
        self._layout.addWidget(self._lower_edit)
        self.setLayout(self._layout)

        self._enable_callback = enable_callback
        self._edit_callback = edit_callback

        self._set_enabled()
        self._enable_checkbox.toggled.connect(self._set_enabled)

    def _bounds_changed(self, val=None):
        upper = self._upper_edit.get_value()
        lower = self._lower_edit.get_value()
        self._edit_callback(upper, lower)

    def _set_enabled(self):
        checked = self._enable_checkbox.isChecked()
        self._upper_edit.setEnabled(checked)
        self._lower_edit.setEnabled(checked)
        self._enable_callback(checked)
        if checked:
            self._bounds_changed()



class DoubleEdit(QtGui.QWidget):
    def __init__(self, default_value, label, callback):
        super (DoubleEdit, self).__init__()
        self._edit_box = QtGui.QLineEdit()
        self._edit_box.setText(str(default_value))
        self._layout = QtGui.QHBoxLayout()
        self._label = QtGui.QLabel(label)
        self._layout.addWidget(self._label)
        self._layout.addWidget(self._edit_box)
        self.setLayout(self._layout)

        self._edit_box.setValidator(QtGui.QDoubleValidator())

        self._edit_box.editingFinished.connect(self._editing_finished)
        self._callback = callback

    def _editing_finished(self):
        value = float(self._edit_box.text())
        self._callback(value)

    def get_value(self):
        return float(self._edit_box.text())

class FilterControl(QtGui.QWidget):
    def __init__(self, default_cutoff, label, filter_type, callback=None, enabled=True):
        super(FilterControl, self).__init__()

        self._filter_type = filter_type
        self._cutoff = default_cutoff

        self._enabled = enabled
        self._enable_box = QtGui.QCheckBox()
        self._enable_box.setChecked(enabled)


        self._label = QtGui.QLabel(label)
        self._label.setFixedWidth(80)


        self._cutoff_edit_box = QtGui.QLineEdit(str(default_cutoff))
        self._cutoff_edit_box.setFixedWidth(50)
        self._cutoff_edit_box.setAlignment(QtCore.Qt.AlignRight)


        self._layout = QtGui.QHBoxLayout()


        self._layout.addWidget(self._label)
        self._layout.addWidget(self._cutoff_edit_box)
        self._layout.addWidget(QtGui.QLabel("Hz"))
        self._layout.addWidget(self._enable_box)
        self.setLayout(self._layout)

        self.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)

        self._controls = [self._label, self._cutoff_edit_box]
        self._change_enabled()

        self._cutoff_edit_box.setValidator(QtGui.QDoubleValidator())

    def connect(self, function):
        self._enable_box.toggled.connect(function)
        self._cutoff_edit_box.textChanged.connect(function)

    def _change_enabled(self):
        for control in self._controls:
            control.setEnabled(self._enable_box.isChecked())

    def get_cutoff(self):
        self._change_enabled()
        if self._enable_box.isChecked():
            return float(self._cutoff_edit_box.text())
        else:
            return None
