from matplotlib.backends import qt4_compat as qt_compat
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore


class ComparisonRangeSetter(QtGui.QWidget):
    def __init__(self):
        super(ComparisonRangeSetter, self).__init__()
        self._layout = QtGui.QGridLayout()
        self._layout.addWidget(QtGui.QLabel("Manual range selection"),0,1)
        self._enable_manual_checkbox = QtGui.QCheckBox()
        self._layout.addWidget(self._enable_manual_checkbox,0,0)
        self.setLayout(self._layout)

class LeadInOutEdit(QtGui.QWidget):
    def __init__(self, default_value, label, callback):
        super (LeadInOutEdit, self).__init__()
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

        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum))

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
