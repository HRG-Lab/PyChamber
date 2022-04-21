import time
from ctypes import util
from typing import List, Optional, Union

import numpy as np
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QDoubleValidator, QFont, QIcon, QIntValidator, QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from quantiphy import Quantity

from pychamber import utils
from pychamber.ui import resources_rc

from .logger import QTextEditLogger
from .mplwidget import MplPolarWidget, MplRectWidget, MplWidget
from .pop_ups import ClearDataWarning

_SIZE_POLICIES = {
    'min_min': QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum),
    'min_pref': QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred),
    'min_exp': QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding),
    'min_fix': QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed),
    'pref_min': QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum),
    'pref_pref': QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred),
    'exp_min': QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum),
    'exp_pref': QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum),
}

_FONTS = {
    'bold_12': QFont('Roboto', 12, QFont.Bold),
    'bold_14': QFont('Roboto', 14, QFont.Bold),
    'bold_20_ibm': QFont('IBM 3270', 20, QFont.Bold),
}


class MainWindow(QMainWindow):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.setWindowTitle("PyChamber")

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.mainWindowLayout = QGridLayout()
        self.centralwidget.setLayout(self.mainWindowLayout)

    def setupUi(self) -> None:
        self.setupAnalyzerGroupBox()
        self.setupPositionerGroupBox()
        self.setupExperimentGroupBox()
        self.setupTabWidget()

        self.updateSizePolicies()
        self.updateFonts()
        self.updateValidators()
        self.initInputs()
        self.initPlots()

        # Convenience methods
        self.update_polar_plot = self.polarPlot.update_plot
        self.update_over_freq_plot = self.overFreqPlot.update_plot

    def closeEvent(self, event) -> None:
        resp = ClearDataWarning(
            ("Are you sure you want to quit?\n" "(Any unsaved data will be LOST)")
        ).warn()
        if resp:
            event.accept()
        else:
            event.ignore()

    @property
    def analyzer_model(self) -> str:
        return self.analyzerModelComboBox.currentText()

    @property
    def analyzer_address(self) -> str:
        return self.analyzerAddressComboBox.currentText()

    @property
    def pol_1(self) -> Optional[List[int]]:
        pol = self.analyzerPol1ComboBox.currentText()
        return [int(pol[1]), int(pol[2])] if pol != "" else None

    @property
    def pol_2(self) -> Optional[List[int]]:
        pol = self.analyzerPol2ComboBox.currentText()
        return [int(pol[1]), int(pol[2])] if pol != "" else None

    @property
    def analyzer_start_freq(self) -> Optional[Quantity]:
        if (f := self.analyzerStartFreqLineEdit.text()) != "":
            return utils.to_freq(f)
        else:
            return None

    @analyzer_start_freq.setter
    def analyzer_start_freq(self, freq: float) -> None:
        f = Quantity(freq, units='Hz')
        self.analyzerStartFreqLineEdit.setText(f.render())

    @property
    def analyzer_stop_freq(self) -> Optional[Quantity]:
        if (f := self.analyzerStopFreqLineEdit.text()) != "":
            return utils.to_freq(f)
        else:
            return None

    @analyzer_stop_freq.setter
    def analyzer_stop_freq(self, freq: float) -> None:
        f = Quantity(freq, units='Hz')
        self.analyzerStopFreqLineEdit.setText(f.render())

    @property
    def analyzer_freq_step(self) -> Optional[Quantity]:
        if (f := self.analyzerStepFreqLineEdit.text()) != "":
            return utils.to_freq(f)
        else:
            return None

    @analyzer_freq_step.setter
    def analyzer_freq_step(self, freq: float) -> None:
        f = Quantity(freq, units='Hz')
        self.analyzerStepFreqLineEdit.setText(f.render())

    @property
    def analyzer_n_points(self) -> Optional[int]:
        if (n := self.analyzerNPointsLineEdit.text()) != "":
            return int(n)
        else:
            return None

    @analyzer_n_points.setter
    def analyzer_n_points(self, n: int) -> None:
        self.analyzerNPointsLineEdit.setText(str(n))

    @property
    def positioner_model(self) -> str:
        return self.positionerModelComboBox.currentText()

    @property
    def positioner_port(self) -> str:
        return self.positionerPortComboBox.currentText()

    @property
    def az_extent_start(self) -> float:
        return self.positionerAzExtentStartSpinBox.value()

    @property
    def az_extent_stop(self) -> float:
        return self.positionerAzExtentStopSpinBox.value()

    @property
    def az_extent_step(self) -> float:
        return self.positionerAzExtentStepSpinBox.value()

    @property
    def el_extent_start(self) -> float:
        return self.positionerElExtentStartSpinBox.value()

    @property
    def el_extent_stop(self) -> float:
        return self.positionerElExtentStopSpinBox.value()

    @property
    def el_extent_step(self) -> float:
        return self.positionerElExtentStepSpinBox.value()

    @property
    def az_jog_step(self) -> float:
        return self.jogAzStepSpinBox.value()

    @property
    def az_jog_to(self) -> Optional[float]:
        try:
            return float(self.jogAzToLineEdit.text())
        except ValueError:
            return None

    @property
    def el_jog_step(self) -> float:
        return self.jogElStepSpinBox.value()

    @property
    def el_jog_to(self) -> Optional[float]:
        try:
            return float(self.jogElToLineEdit.text())
        except ValueError:
            return None

    @property
    def az_pos(self) -> float:
        return float(self.azPositionLineEdit.text())

    @az_pos.setter
    def az_pos(self, pos: Union[float, str]) -> None:
        self.azPositionLineEdit.setText(str(pos))

    @property
    def el_pos(self) -> float:
        return float(self.elPositionLineEdit.text())

    @el_pos.setter
    def el_pos(self, pos: Union[float, str]) -> None:
        self.elPositionLineEdit.setText(str(pos))

    @property
    def total_progress(self) -> int:
        return self.experimentTotalProgressBar.value()

    @total_progress.setter
    def total_progress(self, val: int) -> None:
        self.experimentTotalProgressBar.setValue(val)
        if val == 100:
            self.experimentTotalProgressBar.setFormat("Done!")
        else:
            self.experimentTotalProgressBar.setFormat("%p%")

    @property
    def cut_progress(self) -> int:
        return self.experimentTotalProgressBar.value()

    @cut_progress.setter
    def cut_progress(self, val: int) -> None:
        self.experimentCutProgressBar.setValue(val)

    @property
    def time_remaining(self) -> str:
        return self.experimentTimeRemainingLineEdit.text()

    @time_remaining.setter
    def time_remaining(self, time_: float) -> None:
        if np.isclose(time_, 0):
            self.timeRemainingLineEdit.setText("")
        else:
            time_str = time.strftime("%H hours %M minutes %S seconds", time.gmtime(time_))
            self.timeRemainingLineEdit.setText(time_str)

    @property
    def polar_plot_pol(self) -> int:
        return self.polarPlotPolarizationComboBox.currentIndex()

    @property
    def polar_plot_freq(self) -> float:
        return self.dataPolarFreqSpinBox.cleanText() + self.dataPolarFreqSpinBox.suffix()

    @property
    def polar_plot_min(self) -> float:
        return float(self.polarPlotMinSpinBox.value())

    @property
    def polar_plot_max(self) -> float:
        return float(self.polarPlotMaxSpinBox.value())

    @property
    def polar_plot_step(self) -> float:
        return float(self.polarPlotStepSpinBox.value())

    @property
    def over_freq_plot_pol(self) -> str:
        return self.overFreqPlotPolarizationComboBox.currentText()

    @property
    def over_freq_plot_min(self) -> float:
        return float(self.overFreqPlotMinSpinBox.value())

    @property
    def over_freq_plot_max(self) -> float:
        return float(self.overFreqPlotMaxSpinBox.value())

    @property
    def over_freq_plot_step(self) -> float:
        return float(self.overFreqPlotStepSpinBox.value())

    @property
    def over_freq_plot_az(self) -> float:
        return self.overFreqPlotAzSpinBox.value()

    @property
    def over_freq_plot_el(self) -> float:
        return self.overFreqPlotElSpinBox.value()

    def enable_jog(self) -> None:
        self.jogGroupBox.setEnabled(True)

    def disable_jog(self) -> None:
        self.jogGroupBox.setEnabled(False)

    def enable_jog_buttons(self) -> None:
        self.jogAzLeftButton.setEnabled(True)
        self.jogAzZeroButton.setEnabled(True)
        self.jogAzRightButton.setEnabled(True)
        self.jogAzSubmitButton.setEnabled(True)
        self.jogElUpButton.setEnabled(True)
        self.jogElZeroButton.setEnabled(True)
        self.jogElDownButton.setEnabled(True)
        self.jogElSubmitButton.setEnabled(True)
        self.setZeroButton.setEnabled(True)
        self.returnToZeroButton.setEnabled(True)

    def disable_jog_buttons(self) -> None:
        self.jogAzLeftButton.setEnabled(False)
        self.jogAzZeroButton.setEnabled(False)
        self.jogAzRightButton.setEnabled(False)
        self.jogAzSubmitButton.setEnabled(False)
        self.jogElUpButton.setEnabled(False)
        self.jogElZeroButton.setEnabled(False)
        self.jogElDownButton.setEnabled(False)
        self.jogElSubmitButton.setEnabled(False)
        self.setZeroButton.setEnabled(False)
        self.returnToZeroButton.setEnabled(False)

    def enable_freq(self) -> None:
        self.analyzerFreqGroupBox.setEnabled(True)

    def disable_freq(self) -> None:
        self.analyzerFreqGroupBox.setEnabled(False)

    def enable_experiment(self) -> None:
        if self.analyzerFreqGroupBox.isEnabled() and self.jogGroupBox.isEnabled():
            self.experimentGroupBox.setEnabled(True)

    def disable_experiment(self) -> None:
        self.experimentGroupBox.setEnabled(False)

    def update_polar_plot_freqs(self) -> None:
        start = self.analyzer_start_freq
        stop = self.analyzer_start_freq
        step = self.analyzer_start_freq

        if start:
            self.polarPlotFreqSpinBox.setMinimum(start)
        if stop:
            self.polarPlotFreqSpinBox.setMaximum(stop)
        if step:
            self.polarPlotFreqSpinBox.setMinimum(step)

    def setupAnalyzerGroupBox(self) -> None:
        self.analyzerGroupBox = QGroupBox("Analyzer", self.centralwidget)
        self.analyzerGroupBoxLayout = QVBoxLayout(self.analyzerGroupBox)

        self.analyzerHLayout1 = QHBoxLayout()

        self.analyzerModelLabel = QLabel("Model", self.analyzerGroupBox)
        self.analyzerModelComboBox = QComboBox(self.analyzerGroupBox)
        self.analyzerHLayout1.addWidget(self.analyzerModelLabel)
        self.analyzerHLayout1.addWidget(self.analyzerModelComboBox)

        self.analyzerAddressLabel = QLabel("Address", self.analyzerGroupBox)
        self.analyzerAddressComboBox = QComboBox(self.analyzerGroupBox)
        self.analyzerHLayout1.addWidget(self.analyzerAddressLabel)
        self.analyzerHLayout1.addWidget(self.analyzerAddressComboBox)

        self.analyzerConnectButton = QPushButton("Connect", self.analyzerGroupBox)
        self.analyzerHLayout1.addWidget(self.analyzerConnectButton)

        self.analyzerHLayout2 = QHBoxLayout()

        self.analyzerPol1Label = QLabel("Polarization 1", self.analyzerGroupBox)
        self.analyzerPol1ComboBox = QComboBox(self.analyzerGroupBox)
        self.analyzerHLayout2.addWidget(self.analyzerPol1Label)
        self.analyzerHLayout2.addWidget(self.analyzerPol1ComboBox)

        self.analyzerPol2Label = QLabel("Polarization 2", self.analyzerGroupBox)
        self.analyzerPol2ComboBox = QComboBox(self.analyzerGroupBox)
        self.analyzerHLayout2.addWidget(self.analyzerPol2Label)
        self.analyzerHLayout2.addWidget(self.analyzerPol2ComboBox)

        self.analyzerFreqGroupBox = QGroupBox("Frequency", self.analyzerGroupBox)
        self.analyzerFreqLayout = QGridLayout(self.analyzerFreqGroupBox)

        self.analyzerStartFreqLabel = QLabel("Start", self.analyzerFreqGroupBox)
        self.analyzerStartFreqLineEdit = QLineEdit(self.analyzerFreqGroupBox)
        self.analyzerFreqLayout.addWidget(self.analyzerStartFreqLabel, 0, 0, 1, 1)
        self.analyzerFreqLayout.addWidget(self.analyzerStartFreqLineEdit, 0, 1, 1, 1)

        self.analyzerStopFreqLabel = QLabel("Stop", self.analyzerFreqGroupBox)
        self.analyzerStopFreqLineEdit = QLineEdit(self.analyzerFreqGroupBox)
        self.analyzerFreqLayout.addWidget(self.analyzerStopFreqLabel, 1, 0, 1, 1)
        self.analyzerFreqLayout.addWidget(self.analyzerStopFreqLineEdit, 1, 1, 1, 1)

        self.analyzerStepFreqLabel = QLabel("Step", self.analyzerFreqGroupBox)
        self.analyzerStepFreqLineEdit = QLineEdit(self.analyzerFreqGroupBox)
        self.analyzerFreqLayout.addWidget(self.analyzerStepFreqLabel, 2, 0, 1, 1)
        self.analyzerFreqLayout.addWidget(self.analyzerStepFreqLineEdit, 2, 1, 1, 1)

        self.analyzerNPointsLabel = QLabel("Number of Points", self.analyzerFreqGroupBox)
        self.analyzerNPointsLineEdit = QLineEdit(self.analyzerFreqGroupBox)
        self.analyzerFreqLayout.addWidget(self.analyzerNPointsLabel, 3, 0, 1, 1)
        self.analyzerFreqLayout.addWidget(self.analyzerNPointsLineEdit, 3, 1, 1, 1)

        self.analyzerGroupBoxLayout.addLayout(self.analyzerHLayout1)
        self.analyzerGroupBoxLayout.addLayout(self.analyzerHLayout2)
        self.analyzerGroupBoxLayout.addWidget(self.analyzerFreqGroupBox)

        self.mainWindowLayout.addWidget(self.analyzerGroupBox, 0, 0, 1, 1)
        self.analyzerFreqGroupBox.setEnabled(False)

    def setupPositionerGroupBox(self) -> None:
        self.positionerGroupBox = QGroupBox("Positioner", self.centralwidget)
        self.positionerGroupBoxLayout = QVBoxLayout(self.positionerGroupBox)

        self.positionerHLayout1 = QHBoxLayout()
        self.positionerModelLabel = QLabel("Model", self.positionerGroupBox)
        self.positionerModelComboBox = QComboBox(self.positionerGroupBox)
        self.positionerHLayout1.addWidget(self.positionerModelLabel)
        self.positionerHLayout1.addWidget(self.positionerModelComboBox)

        self.positionerPortLabel = QLabel("Port", self.positionerGroupBox)
        self.positionerPortComboBox = QComboBox(self.positionerGroupBox)
        self.positionerHLayout1.addWidget(self.positionerPortLabel)
        self.positionerHLayout1.addWidget(self.positionerPortComboBox)

        self.positionerConnectButton = QPushButton("Connect", self.positionerGroupBox)
        self.positionerHLayout1.addWidget(self.positionerConnectButton)
        self.positionerGroupBoxLayout.addLayout(self.positionerHLayout1)

        self.positionerExtentsGroupBox = QGroupBox(self.positionerGroupBox)
        self.positionerExtentsGroupBoxLayout = QHBoxLayout(self.positionerExtentsGroupBox)
        self.setupAzExtentWidgets()
        self.setupElExtentWidgets()
        self.positionerGroupBoxLayout.addWidget(self.positionerExtentsGroupBox)

        self.jogGroupBox = QGroupBox(self.positionerGroupBox)
        self.jogGroupBoxLayout = QVBoxLayout(self.jogGroupBox)
        self.setupJogBox()
        self.positionerGroupBoxLayout.addWidget(self.jogGroupBox)

        self.mainWindowLayout.addWidget(self.positionerGroupBox, 1, 0, 1, 1)

    def setupAzExtentWidgets(self) -> None:
        self.positionerAzExtentLayout = QVBoxLayout()
        self.positionerAzExtentLabel = QLabel("Azimuth", self.positionerExtentsGroupBox)
        self.positionerAzExtentPlot = MplPolarWidget(
            'tab:blue', self.positionerExtentsGroupBox
        )
        self.positionerAzExtentLayout.addWidget(self.positionerAzExtentLabel)
        self.positionerAzExtentLayout.addWidget(self.positionerAzExtentPlot)

        self.positionerAzStartHLayout = QHBoxLayout()
        self.positionerAzExtentStartLabel = QLabel(
            "Start", self.positionerExtentsGroupBox
        )
        self.positionerAzExtentStartSpinBox = QDoubleSpinBox(
            self.positionerExtentsGroupBox
        )
        self.positionerAzStartHLayout.addWidget(self.positionerAzExtentStartLabel)
        self.positionerAzStartHLayout.addWidget(self.positionerAzExtentStartSpinBox)
        self.positionerAzExtentLayout.addLayout(self.positionerAzStartHLayout)

        self.positionerAzStopHLayout = QHBoxLayout()
        self.positionerAzExtentStopLabel = QLabel("Stop", self.positionerExtentsGroupBox)
        self.positionerAzExtentStopSpinBox = QDoubleSpinBox(
            self.positionerExtentsGroupBox
        )
        self.positionerAzStopHLayout.addWidget(self.positionerAzExtentStopLabel)
        self.positionerAzStopHLayout.addWidget(self.positionerAzExtentStopSpinBox)
        self.positionerAzExtentLayout.addLayout(self.positionerAzStopHLayout)

        self.positionerAzStepHLayout = QHBoxLayout()
        self.positionerAzExtentStepLabel = QLabel("Step", self.positionerExtentsGroupBox)
        self.positionerAzExtentStepSpinBox = QDoubleSpinBox(
            self.positionerExtentsGroupBox
        )
        self.positionerAzStepHLayout.addWidget(self.positionerAzExtentStepLabel)
        self.positionerAzStepHLayout.addWidget(self.positionerAzExtentStepSpinBox)
        self.positionerAzExtentLayout.addLayout(self.positionerAzStepHLayout)

        self.positionerExtentsGroupBoxLayout.addLayout(self.positionerAzExtentLayout)

    def setupElExtentWidgets(self) -> None:
        self.positionerElExtentLayout = QVBoxLayout()
        self.positionerElExtentLabel = QLabel("Elevation", self.positionerExtentsGroupBox)
        self.positionerElExtentPlot = MplPolarWidget(
            'tab:orange', self.positionerExtentsGroupBox
        )
        self.positionerElExtentLayout.addWidget(self.positionerElExtentLabel)
        self.positionerElExtentLayout.addWidget(self.positionerElExtentPlot)

        self.positionerElStartHLayout = QHBoxLayout()
        self.positionerElExtentStartLabel = QLabel(
            "Start", self.positionerExtentsGroupBox
        )
        self.positionerElExtentStartSpinBox = QDoubleSpinBox(
            self.positionerExtentsGroupBox
        )
        self.positionerElStartHLayout.addWidget(self.positionerElExtentStartLabel)
        self.positionerElStartHLayout.addWidget(self.positionerElExtentStartSpinBox)
        self.positionerElExtentLayout.addLayout(self.positionerElStartHLayout)

        self.positionerElStopHLayout = QHBoxLayout()
        self.positionerElExtentStopLabel = QLabel("Stop", self.positionerExtentsGroupBox)
        self.positionerElExtentStopSpinBox = QDoubleSpinBox(
            self.positionerExtentsGroupBox
        )
        self.positionerElStopHLayout.addWidget(self.positionerElExtentStopLabel)
        self.positionerElStopHLayout.addWidget(self.positionerElExtentStopSpinBox)
        self.positionerElExtentLayout.addLayout(self.positionerElStopHLayout)

        self.positionerElStepHLayout = QHBoxLayout()
        self.positionerElExtentStepLabel = QLabel("Step", self.positionerExtentsGroupBox)
        self.positionerElExtentStepSpinBox = QDoubleSpinBox(
            self.positionerExtentsGroupBox
        )
        self.positionerElStepHLayout.addWidget(self.positionerElExtentStepLabel)
        self.positionerElStepHLayout.addWidget(self.positionerElExtentStepSpinBox)
        self.positionerElExtentLayout.addLayout(self.positionerElStepHLayout)

        self.positionerExtentsGroupBoxLayout.addLayout(self.positionerElExtentLayout)

    def setupJogBox(self) -> None:
        self.jogButtonsLayout = QGridLayout()

        self.jogAzLabel = QLabel("Azimuth", self.jogGroupBox)
        self.jogAzStepLabel = QLabel("Step", self.jogGroupBox)
        self.jogAzToLabel = QLabel("Jog Azimuth To", self.jogGroupBox)
        self.jogAzLeftButton = QPushButton(self.jogGroupBox)
        self.jogAzLeftButton.setIcon(QIcon(QPixmap(":/icons/icons/LeftArrow.png")))
        self.jogAzLeftButton.setIconSize(QSize(32, 32))
        self.jogAzZeroButton = QPushButton(self.jogGroupBox)
        self.jogAzRightButton = QPushButton(self.jogGroupBox)
        self.jogAzRightButton.setIcon(QIcon(QPixmap(":/icons/icons/RightArrow.png")))
        self.jogAzRightButton.setIconSize(QSize(32, 32))
        self.jogAzSubmitButton = QPushButton(self.jogGroupBox)
        self.jogAzSubmitButton.setIcon(QIcon(QPixmap(":/icons/icons/Check.png")))
        self.jogAzSubmitButton.setIconSize(QSize(32, 32))
        self.jogAzStepSpinBox = QDoubleSpinBox(self.jogGroupBox)
        self.jogAzToLineEdit = QLineEdit(self.jogGroupBox)

        self.jogButtonsLayout.addWidget(self.jogAzLabel, 0, 0, 1, 3)
        self.jogButtonsLayout.addWidget(self.jogAzStepLabel, 0, 3, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogAzToLabel, 0, 4, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogAzLeftButton, 1, 0, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogAzZeroButton, 1, 1, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogAzRightButton, 1, 2, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogAzStepSpinBox, 1, 3, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogAzToLineEdit, 1, 4, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogAzSubmitButton, 1, 5, 1, 1)

        self.jogElLabel = QLabel("Elevation", self.jogGroupBox)
        self.jogElStepLabel = QLabel("Step", self.jogGroupBox)
        self.jogElToLabel = QLabel("Jog Elevation To", self.jogGroupBox)
        self.jogElUpButton = QPushButton("", self.jogGroupBox)
        self.jogElUpButton.setIcon(QIcon(QPixmap(":/icons/icons/UpArrow.png")))
        self.jogElUpButton.setIconSize(QSize(32, 32))
        self.jogElZeroButton = QPushButton("", self.jogGroupBox)
        self.jogElDownButton = QPushButton("", self.jogGroupBox)
        self.jogElDownButton.setIcon(QIcon(QPixmap(":/icons/icons/DownArrow.png")))
        self.jogElDownButton.setIconSize(QSize(32, 32))
        self.jogElSubmitButton = QPushButton("", self.jogGroupBox)
        self.jogElSubmitButton.setIcon(QIcon(QPixmap(":/icons/icons/Check.png")))
        self.jogElSubmitButton.setIconSize(QSize(32, 32))
        self.jogElStepSpinBox = QDoubleSpinBox(self.jogGroupBox)
        self.jogElToLineEdit = QLineEdit(self.jogGroupBox)

        self.jogButtonsLayout.addWidget(self.jogElLabel, 2, 0, 1, 3)
        self.jogButtonsLayout.addWidget(self.jogElStepLabel, 2, 3, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogElToLabel, 2, 4, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogElUpButton, 3, 0, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogElZeroButton, 3, 1, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogElDownButton, 3, 2, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogElStepSpinBox, 3, 3, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogElToLineEdit, 3, 4, 1, 1)
        self.jogButtonsLayout.addWidget(self.jogElSubmitButton, 3, 5, 1, 1)

        self.jogGroupBoxLayout.addLayout(self.jogButtonsLayout)

        self.positionerPosLayout = QHBoxLayout()
        self.azPositionLayout = QVBoxLayout()
        self.azPositionLabel = QLabel("Azimuth", self.jogGroupBox)
        self.azPositionLineEdit = QLineEdit(self.jogGroupBox)
        self.azPositionLineEdit.setReadOnly(True)
        self.azPositionLayout.addWidget(self.azPositionLabel)
        self.azPositionLayout.addWidget(self.azPositionLineEdit)

        self.elPositionLayout = QVBoxLayout()
        self.elPositionLabel = QLabel("Elevation", self.jogGroupBox)
        self.elPositionLineEdit = QLineEdit(self.jogGroupBox)
        self.elPositionLineEdit.setReadOnly(True)
        self.elPositionLayout.addWidget(self.elPositionLabel)
        self.elPositionLayout.addWidget(self.elPositionLineEdit)

        self.zeroButtonLayout = QHBoxLayout()
        self.setZeroButton = QPushButton("Set 0,0", self.jogGroupBox)
        self.returnToZeroButton = QPushButton("Return to 0,0", self.jogGroupBox)
        self.zeroButtonLayout.addWidget(self.setZeroButton)
        self.zeroButtonLayout.addWidget(self.returnToZeroButton)

        self.positionerPosLayout.addLayout(self.azPositionLayout)
        self.positionerPosLayout.addLayout(self.elPositionLayout)
        self.jogGroupBoxLayout.addLayout(self.positionerPosLayout)
        self.jogGroupBoxLayout.addLayout(self.zeroButtonLayout)

        self.jogGroupBox.setEnabled(False)

    def setupExperimentGroupBox(self) -> None:
        self.experimentGroupBox = QGroupBox("Experiment", self.centralwidget)
        self.experimentGroupBoxLayout = QHBoxLayout(self.experimentGroupBox)

        self.experimentButtonVLayout = QVBoxLayout()
        self.experimentFullScanButton = QPushButton("Full Scan", self.experimentGroupBox)
        self.experimentAzScanButton = QPushButton("Scan Azimuth", self.experimentGroupBox)
        self.experimentElScanButton = QPushButton(
            "Scan Elevation", self.experimentGroupBox
        )
        self.experimentAbortButton = QPushButton("ABORT", self.experimentGroupBox)
        self.experimentAbortButton.setStyleSheet("background-color: rgb(237, 51, 59)")
        self.experimentButtonVLayout.addWidget(self.experimentFullScanButton)
        self.experimentButtonVLayout.addWidget(self.experimentAzScanButton)
        self.experimentButtonVLayout.addWidget(self.experimentElScanButton)
        self.experimentButtonVLayout.addWidget(self.experimentAbortButton)

        self.experimentProgressVLayout = QVBoxLayout()
        self.experimentTotalProgressLabel = QLabel(
            "Total Progress", self.experimentGroupBox
        )
        self.experimentTotalProgressBar = QProgressBar(self.experimentGroupBox)
        self.experimentProgressVLayout.addWidget(self.experimentTotalProgressLabel)
        self.experimentProgressVLayout.addWidget(self.experimentTotalProgressBar)

        self.experimentCutProgressLabel = QLabel("Cut Progress", self.experimentGroupBox)
        self.experimentCutProgressBar = QProgressBar(self.experimentGroupBox)
        self.experimentProgressVLayout.addWidget(self.experimentCutProgressLabel)
        self.experimentProgressVLayout.addWidget(self.experimentCutProgressBar)

        self.experimentTimeRemainingLabel = QLabel(
            "Time Remaining Estimate", self.experimentGroupBox
        )
        self.experimentTimeRemainingLineEdit = QLineEdit(self.experimentGroupBox)
        self.experimentProgressVLayout.addWidget(self.experimentTimeRemainingLabel)
        self.experimentProgressVLayout.addWidget(self.experimentTimeRemainingLineEdit)

        self.experimentGroupBoxLayout.addLayout(self.experimentButtonVLayout)
        self.experimentGroupBoxLayout.addLayout(self.experimentProgressVLayout)

        self.mainWindowLayout.addWidget(self.experimentGroupBox, 0, 1, 1, 1)
        self.experimentGroupBox.setEnabled(False)
        self.experimentCutProgressLabel.hide()
        self.experimentCutProgressBar.hide()

    def setupTabWidget(self) -> None:
        self.tabWidget = QTabWidget(self.centralwidget)
        self.polarPlotTab = QWidget(self.tabWidget)
        self.overFreqPlotTab = QWidget(self.tabWidget)
        self.calibrationTab = QWidget(self.tabWidget)
        self.dataTab = QWidget(self.tabWidget)
        self.logTab = QWidget(self.tabWidget)

        self.tabWidget.addTab(self.polarPlotTab, "Polar Plot")
        self.tabWidget.addTab(self.overFreqPlotTab, "Over Frequency Plot")
        self.tabWidget.addTab(self.calibrationTab, "Calibration")
        self.tabWidget.addTab(self.dataTab, "Data")
        self.tabWidget.addTab(self.logTab, "Log")

        self.setupPolarPlotTab()
        self.setupOverFreqPlotTab()
        self.setupCalibrationTab()
        self.setupDataTab()
        self.setupLogTab()

        self.mainWindowLayout.addWidget(self.tabWidget, 1, 1, 1, 1)

    def setupPolarPlotTab(self) -> None:
        tab = self.polarPlotTab
        self.polarPlotTabLayout = QVBoxLayout(tab)

        self.polarPlotSettingsHLayout = QHBoxLayout()
        self.polarPlotPolarizationLabel = QLabel("Polarization", tab)
        self.polarPlotPolarizationComboBox = QComboBox(tab)
        self.polarPlotPolarizationComboBox.addItems(['1', '2'])
        self.polarPlotFreqLabel = QLabel("Frequency", tab)
        self.polarPlotFreqSpinBox = QDoubleSpinBox(tab)
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.polarPlotMinLabel = QLabel("Min", tab)
        self.polarPlotMinSpinBox = QSpinBox(tab)
        self.polarPlotMaxLabel = QLabel("Max", tab)
        self.polarPlotMaxSpinBox = QSpinBox(tab)
        self.polarPlotStepLabel = QLabel("dB/div", tab)
        self.polarPlotStepSpinBox = QSpinBox(tab)

        self.polarPlotSettingsHLayout.addWidget(self.polarPlotPolarizationLabel)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotPolarizationComboBox)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotFreqLabel)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotFreqSpinBox)
        self.polarPlotSettingsHLayout.addItem(spacer)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotMinLabel)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotMinSpinBox)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotMaxLabel)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotMaxSpinBox)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotStepLabel)
        self.polarPlotSettingsHLayout.addWidget(self.polarPlotStepSpinBox)
        self.polarPlotTabLayout.addLayout(self.polarPlotSettingsHLayout)

        self.polarPlot = MplPolarWidget('tab:blue', tab)
        self.polarPlotTabLayout.addWidget(self.polarPlot)

    def setupOverFreqPlotTab(self) -> None:
        tab = self.overFreqPlotTab
        self.overFreqPlotTabLayout = QVBoxLayout(tab)

        self.overFreqPlotSettingsHLayout1 = QHBoxLayout()
        self.overFreqPlotPolarizationLabel = QLabel("Polarization", tab)
        self.overFreqPlotPolarizationComboBox = QComboBox(tab)
        self.overFreqPlotPolarizationComboBox.addItems(['1', '2'])
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.overFreqPlotMinLabel = QLabel("Min", tab)
        self.overFreqPlotMinSpinBox = QSpinBox(tab)
        self.overFreqPlotMaxLabel = QLabel("Max", tab)
        self.overFreqPlotMaxSpinBox = QSpinBox(tab)
        self.overFreqPlotStepLabel = QLabel("dB/div", tab)
        self.overFreqPlotStepSpinBox = QSpinBox(tab)

        self.overFreqPlotSettingsHLayout1.addWidget(self.overFreqPlotPolarizationLabel)
        self.overFreqPlotSettingsHLayout1.addWidget(self.overFreqPlotPolarizationComboBox)
        self.overFreqPlotSettingsHLayout1.addItem(spacer)
        self.overFreqPlotSettingsHLayout1.addWidget(self.overFreqPlotMinLabel)
        self.overFreqPlotSettingsHLayout1.addWidget(self.overFreqPlotMinSpinBox)
        self.overFreqPlotSettingsHLayout1.addWidget(self.overFreqPlotMaxLabel)
        self.overFreqPlotSettingsHLayout1.addWidget(self.overFreqPlotMaxSpinBox)
        self.overFreqPlotSettingsHLayout1.addWidget(self.overFreqPlotStepLabel)
        self.overFreqPlotSettingsHLayout1.addWidget(self.overFreqPlotStepSpinBox)

        self.overFreqPlotSettingsHLayout2 = QHBoxLayout()
        self.overFreqPlotAzLabel = QLabel("Azimuth", tab)
        self.overFreqPlotAzSpinBox = QDoubleSpinBox(tab)
        self.overFreqPlotElLabel = QLabel("Elevation", tab)
        self.overFreqPlotElSpinBox = QDoubleSpinBox(tab)
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.overFreqPlotSettingsHLayout2.addWidget(self.overFreqPlotAzLabel)
        self.overFreqPlotSettingsHLayout2.addWidget(self.overFreqPlotAzSpinBox)
        self.overFreqPlotSettingsHLayout2.addWidget(self.overFreqPlotElLabel)
        self.overFreqPlotSettingsHLayout2.addWidget(self.overFreqPlotElSpinBox)
        self.overFreqPlotSettingsHLayout2.addItem(spacer)

        self.overFreqPlotTabLayout.addLayout(self.overFreqPlotSettingsHLayout1)
        self.overFreqPlotTabLayout.addLayout(self.overFreqPlotSettingsHLayout2)

        self.overFreqPlot = MplRectWidget('tab:blue', tab)
        self.overFreqPlotTabLayout.addWidget(self.overFreqPlot)

    def setupCalibrationTab(self) -> None:
        pass

    def setupDataTab(self) -> None:
        tab = self.dataTab
        self.dataTabLayout = QGridLayout(tab)

        self.dataTabVLayout = QVBoxLayout()

        self.clearDataButton = QPushButton("Clear Data", tab)
        self.clearDataButton.setStyleSheet("background-color: rgb(237, 51, 59)")
        self.saveDataButton = QPushButton("Save Data", tab)
        self.loadDataButton = QPushButton("Load Data", tab)
        self.exportDataButton = QPushButton("Export Data", tab)
        self.dataTabVLayout.addWidget(self.clearDataButton)
        self.dataTabVLayout.addWidget(self.saveDataButton)
        self.dataTabVLayout.addWidget(self.loadDataButton)
        self.dataTabVLayout.addWidget(self.exportDataButton)
        self.dataTabLayout.addLayout(self.dataTabVLayout, 1, 1, 1, 1)

        vspacer_1 = QSpacerItem(20, 200, QSizePolicy.Minimum, QSizePolicy.Preferred)
        vspacer_2 = QSpacerItem(20, 200, QSizePolicy.Minimum, QSizePolicy.Preferred)
        hspacer_1 = QSpacerItem(200, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)
        hspacer_2 = QSpacerItem(200, 20, QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.dataTabLayout.addItem(vspacer_1, 0, 1, 1, 1)
        self.dataTabLayout.addItem(vspacer_2, 2, 1, 1, 1)
        self.dataTabLayout.addItem(hspacer_1, 1, 0, 1, 1)
        self.dataTabLayout.addItem(hspacer_2, 1, 2, 1, 1)

    def setupLogTab(self) -> None:
        self.logTabLayout = QVBoxLayout(self.logTab)
        self.logger = QTextEditLogger(self.logTab)
        self.logTabLayout.addWidget(self.logger.widget)

    def updateSizePolicies(self) -> None:
        self.analyzerModelLabel.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.analyzerModelComboBox.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.analyzerAddressLabel.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.analyzerAddressComboBox.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.analyzerConnectButton.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.analyzerPol1Label.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.analyzerPol1ComboBox.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.analyzerPol2Label.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.analyzerPol2ComboBox.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.analyzerFreqGroupBox.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.analyzerStartFreqLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.analyzerStopFreqLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.analyzerStepFreqLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.analyzerNPointsLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.analyzerStartFreqLineEdit.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.analyzerStopFreqLineEdit.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.analyzerStepFreqLineEdit.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.analyzerNPointsLineEdit.setSizePolicy(_SIZE_POLICIES['exp_pref'])

        self.positionerModelLabel.setSizePolicy(_SIZE_POLICIES["min_pref"])
        self.positionerModelComboBox.setSizePolicy(_SIZE_POLICIES["exp_pref"])
        self.positionerPortLabel.setSizePolicy(_SIZE_POLICIES["min_pref"])
        self.positionerPortComboBox.setSizePolicy(_SIZE_POLICIES["exp_pref"])
        self.positionerConnectButton.setSizePolicy(_SIZE_POLICIES["min_pref"])

        self.positionerAzExtentPlot.setSizePolicy(_SIZE_POLICIES["pref_pref"])
        self.positionerAzExtentPlot.setMinimumSize(QSize(200, 200))
        self.positionerAzExtentPlot.setMaximumSize(QSize(250, 250))
        self.positionerElExtentPlot.setSizePolicy(_SIZE_POLICIES["pref_pref"])
        self.positionerElExtentPlot.setMinimumSize(QSize(200, 200))
        self.positionerElExtentPlot.setMaximumSize(QSize(250, 250))

        self.jogAzLabel.setSizePolicy(_SIZE_POLICIES['pref_min'])
        self.jogAzStepLabel.setSizePolicy(_SIZE_POLICIES['pref_min'])
        self.jogAzToLabel.setSizePolicy(_SIZE_POLICIES['pref_min'])
        self.jogAzLeftButton.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.jogAzZeroButton.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.jogAzRightButton.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.jogAzStepSpinBox.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.jogAzToLineEdit.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.jogAzSubmitButton.setSizePolicy(_SIZE_POLICIES['min_pref'])

        self.jogElLabel.setSizePolicy(_SIZE_POLICIES['pref_min'])
        self.jogElStepLabel.setSizePolicy(_SIZE_POLICIES['pref_min'])
        self.jogElToLabel.setSizePolicy(_SIZE_POLICIES['pref_min'])
        self.jogElUpButton.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.jogElZeroButton.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.jogElDownButton.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.jogElStepSpinBox.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.jogElToLineEdit.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.jogElSubmitButton.setSizePolicy(_SIZE_POLICIES['min_pref'])

        self.azPositionLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.azPositionLineEdit.setSizePolicy(_SIZE_POLICIES['min_pref'])
        self.elPositionLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.elPositionLineEdit.setSizePolicy(_SIZE_POLICIES['min_pref'])

        self.experimentFullScanButton.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.experimentAzScanButton.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.experimentElScanButton.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.experimentAbortButton.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.experimentTotalProgressLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.experimentTotalProgressBar.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.experimentCutProgressLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.experimentCutProgressBar.setSizePolicy(_SIZE_POLICIES['exp_pref'])
        self.experimentTimeRemainingLabel.setSizePolicy(_SIZE_POLICIES['pref_pref'])
        self.experimentTimeRemainingLineEdit.setSizePolicy(_SIZE_POLICIES['exp_pref'])

        self.mainWindowLayout.setColumnStretch(0, 0)
        self.mainWindowLayout.setColumnStretch(1, 2)

    def updateFonts(self) -> None:
        self.positionerAzExtentLabel.setFont(_FONTS["bold_14"])
        self.positionerAzExtentLabel.setAlignment(Qt.AlignHCenter)
        self.positionerElExtentLabel.setFont(_FONTS["bold_14"])
        self.positionerElExtentLabel.setAlignment(Qt.AlignHCenter)

        self.jogAzLabel.setFont(_FONTS["bold_12"])
        self.jogAzLabel.setAlignment(Qt.AlignHCenter)
        self.jogAzStepLabel.setFont(_FONTS["bold_12"])
        self.jogAzStepLabel.setAlignment(Qt.AlignHCenter)
        self.jogAzToLabel.setFont(_FONTS["bold_12"])
        self.jogAzToLabel.setAlignment(Qt.AlignHCenter)
        self.jogElLabel.setFont(_FONTS["bold_12"])
        self.jogElLabel.setAlignment(Qt.AlignHCenter)
        self.jogElStepLabel.setFont(_FONTS["bold_12"])
        self.jogElStepLabel.setAlignment(Qt.AlignHCenter)
        self.jogElToLabel.setFont(_FONTS["bold_12"])
        self.jogElToLabel.setAlignment(Qt.AlignHCenter)

        self.azPositionLabel.setFont(_FONTS["bold_12"])
        self.azPositionLabel.setAlignment(Qt.AlignHCenter)
        self.azPositionLineEdit.setFont(_FONTS["bold_20_ibm"])
        self.elPositionLabel.setFont(_FONTS["bold_12"])
        self.elPositionLabel.setAlignment(Qt.AlignHCenter)
        self.elPositionLineEdit.setFont(_FONTS["bold_20_ibm"])

        self.experimentFullScanButton.setFont(_FONTS["bold_12"])
        self.experimentAzScanButton.setFont(_FONTS["bold_12"])
        self.experimentElScanButton.setFont(_FONTS["bold_12"])
        self.experimentAbortButton.setFont(_FONTS["bold_12"])

        self.experimentTotalProgressLabel.setFont(_FONTS["bold_12"])
        self.experimentTotalProgressLabel.setAlignment(Qt.AlignHCenter)
        self.experimentCutProgressLabel.setFont(_FONTS["bold_12"])
        self.experimentCutProgressLabel.setAlignment(Qt.AlignHCenter)
        self.experimentTimeRemainingLabel.setFont(_FONTS["bold_12"])
        self.experimentTimeRemainingLabel.setAlignment(Qt.AlignHCenter)

    def updateValidators(self) -> None:
        self.jogAzToLineEdit.setValidator(QDoubleValidator(-360.0, 360.0, 2))
        self.jogElToLineEdit.setValidator(QDoubleValidator(-360.0, 360.0, 2))

        self.analyzerNPointsLineEdit.setValidator(QIntValidator())

    def initInputs(self) -> None:
        self.positionerAzExtentStartSpinBox.setMinimum(-180.0)
        self.positionerAzExtentStartSpinBox.setMaximum(180.0)
        self.positionerAzExtentStartSpinBox.setSingleStep(1.0)
        self.positionerAzExtentStartSpinBox.setDecimals(2)
        self.positionerAzExtentStartSpinBox.setValue(-90.0)

        self.positionerAzExtentStopSpinBox.setMinimum(-180.0)
        self.positionerAzExtentStopSpinBox.setMaximum(180.0)
        self.positionerAzExtentStopSpinBox.setSingleStep(1.0)
        self.positionerAzExtentStopSpinBox.setDecimals(2)
        self.positionerAzExtentStopSpinBox.setValue(90.0)

        self.positionerAzExtentStepSpinBox.setMinimum(0.0)
        self.positionerAzExtentStepSpinBox.setMaximum(360.0)
        self.positionerAzExtentStepSpinBox.setSingleStep(1.0)
        self.positionerAzExtentStepSpinBox.setDecimals(2)
        self.positionerAzExtentStepSpinBox.setValue(5.0)

        self.positionerElExtentStartSpinBox.setMinimum(-180.0)
        self.positionerElExtentStartSpinBox.setMaximum(180.0)
        self.positionerElExtentStartSpinBox.setSingleStep(1.0)
        self.positionerElExtentStartSpinBox.setDecimals(2)
        self.positionerElExtentStartSpinBox.setValue(-90.0)

        self.positionerElExtentStopSpinBox.setMinimum(-180.0)
        self.positionerElExtentStopSpinBox.setMaximum(180.0)
        self.positionerElExtentStopSpinBox.setSingleStep(1.0)
        self.positionerElExtentStopSpinBox.setDecimals(2)
        self.positionerElExtentStopSpinBox.setValue(90.0)

        self.positionerElExtentStepSpinBox.setMinimum(0.0)
        self.positionerElExtentStepSpinBox.setMaximum(360.0)
        self.positionerElExtentStepSpinBox.setSingleStep(1.0)
        self.positionerElExtentStepSpinBox.setDecimals(2)
        self.positionerElExtentStepSpinBox.setValue(5.0)

        self.jogAzStepSpinBox.setMinimum(0.0)
        self.jogAzStepSpinBox.setMaximum(90.0)
        self.jogAzStepSpinBox.setSingleStep(0.25)
        self.jogAzStepSpinBox.setDecimals(2)
        self.jogAzStepSpinBox.setValue(0.0)

        self.jogElStepSpinBox.setMinimum(0.0)
        self.jogElStepSpinBox.setMaximum(90.0)
        self.jogElStepSpinBox.setSingleStep(0.25)
        self.jogElStepSpinBox.setDecimals(2)
        self.jogElStepSpinBox.setValue(0.0)

        self.jogAzToLineEdit.setPlaceholderText("0.0")
        self.jogElToLineEdit.setPlaceholderText("0.0")

        self.polarPlotMinSpinBox.setMinimum(-100)
        self.polarPlotMinSpinBox.setMaximum(100)
        self.polarPlotMinSpinBox.setSingleStep(5)
        self.polarPlotMinSpinBox.setValue(-30)

        self.polarPlotMaxSpinBox.setMinimum(-100)
        self.polarPlotMaxSpinBox.setMaximum(100)
        self.polarPlotMaxSpinBox.setSingleStep(5)
        self.polarPlotMaxSpinBox.setValue(0)

        self.polarPlotStepSpinBox.setMinimum(1)
        self.polarPlotStepSpinBox.setMaximum(100)
        self.polarPlotStepSpinBox.setSingleStep(10)
        self.polarPlotStepSpinBox.setValue(10)

        self.overFreqPlotMinSpinBox.setMinimum(-100)
        self.overFreqPlotMinSpinBox.setMaximum(100)
        self.overFreqPlotMinSpinBox.setSingleStep(5)
        self.overFreqPlotMinSpinBox.setValue(-30)

        self.overFreqPlotMaxSpinBox.setMinimum(-100)
        self.overFreqPlotMaxSpinBox.setMaximum(100)
        self.overFreqPlotMaxSpinBox.setSingleStep(5)
        self.overFreqPlotMaxSpinBox.setValue(0)

        self.overFreqPlotStepSpinBox.setMinimum(1)
        self.overFreqPlotStepSpinBox.setMaximum(100)
        self.overFreqPlotStepSpinBox.setSingleStep(10)
        self.overFreqPlotStepSpinBox.setValue(10)

    def initPlots(self) -> None:
        self.positionerAzExtentPlot.ticks = False
        self.positionerAzExtentPlot.grid = False
        self.positionerAzExtentStartSpinBox.valueChanged.connect(
            self.update_az_extent_plot
        )
        self.positionerAzExtentStopSpinBox.valueChanged.connect(
            self.update_az_extent_plot
        )
        self.positionerAzExtentStepSpinBox.valueChanged.connect(
            self.update_az_extent_plot
        )
        self.update_az_extent_plot()

        self.positionerElExtentPlot.ticks = False
        self.positionerElExtentPlot.grid = False
        self.positionerElExtentStartSpinBox.valueChanged.connect(
            self.update_el_extent_plot
        )
        self.positionerElExtentStopSpinBox.valueChanged.connect(
            self.update_el_extent_plot
        )
        self.positionerElExtentStepSpinBox.valueChanged.connect(
            self.update_el_extent_plot
        )
        self.update_el_extent_plot()

        self.polarPlot.set_scale(
            min=self.polar_plot_min, max=self.polar_plot_max, step=self.polar_plot_step
        )
        self.polarPlotMinSpinBox.valueChanged.connect(self.polarPlot.set_scale_min)
        self.polarPlotMaxSpinBox.valueChanged.connect(self.polarPlot.set_scale_max)
        self.polarPlotStepSpinBox.valueChanged.connect(self.polarPlot.set_scale_step)

        self.overFreqPlot.set_scale(
            min=self.over_freq_plot_min,
            max=self.over_freq_plot_max,
            step=self.over_freq_plot_step,
        )
        self.overFreqPlotMinSpinBox.valueChanged.connect(self.overFreqPlot.set_scale_min)
        self.overFreqPlotMaxSpinBox.valueChanged.connect(self.overFreqPlot.set_scale_max)
        self.overFreqPlotStepSpinBox.valueChanged.connect(
            self.overFreqPlot.set_scale_step
        )

    def update_az_extent_plot(self) -> None:
        start = np.deg2rad(self.az_extent_start)
        stop = np.deg2rad(self.az_extent_stop)
        step = np.deg2rad(self.az_extent_step)

        thetas = np.arange(start, stop + np.deg2rad(1), step)
        rs = [0, 1] * len(thetas)
        thetas = np.repeat(thetas, 2)
        self.positionerAzExtentPlot.update_plot(thetas, np.array(rs), redraw=True)

    def update_el_extent_plot(self) -> None:
        start = np.deg2rad(self.el_extent_start)
        stop = np.deg2rad(self.el_extent_stop)
        step = np.deg2rad(self.el_extent_step)

        thetas = np.arange(start, stop + np.deg2rad(1), step)
        rs = [0, 1] * len(thetas)
        thetas = np.repeat(thetas, 2)
        self.positionerElExtentPlot.update_plot(thetas, np.array(rs), redraw=True)