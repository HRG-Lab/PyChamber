"""Qt5 MatPlotLib Widget.

    isort:skip_file
"""

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QSizePolicy, QWidget, QVBoxLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.ticker import EngFormatter

import matplotlib
import numpy as np

matplotlib.use('QT5Agg')


class MplCanvas(Canvas):
    def __init__(self):
        self.fig = Figure()
        Canvas.__init__(self, self.fig)
        Canvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        Canvas.updateGeometry(self)


class MplWidget(QWidget):
    def __init__(self, color: str, parent=None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

        self._grid = True
        self.color = color

    @property
    def grid(self) -> bool:
        return self._grid

    @grid.setter
    def grid(self, setting: bool) -> None:
        self._grid = setting

    def sizeHint(self) -> QSize:
        return QSize(300, 300)


class MplRectWidget(MplWidget):
    def __init__(self, color: str, parent=None):
        super(MplRectWidget, self).__init__(color, parent)

        self.ax = self.canvas.fig.add_subplot()
        self.artist, *_ = self.ax.plot(np.array([0]), np.array([0]), color=self.color)
        self.ax.grid(self.grid)
        self.xformatter = EngFormatter(unit='Hz')
        self.xtitle = ""
        self.ytitle = ""

        # Semi-sensible defaults
        self.ymin = -30.0
        self.ymax = 0.0
        self.ystep = 10.0

    def update_plot(self, xdata: np.ndarray, ydata: np.ndarray) -> None:
        self.ax.cla()
        self.artist, *_ = self.ax.plot(xdata, ydata, color=self.color)
        self.ax.grid(self.grid)
        self.ax.xaxis.set_major_formatter(self.xformatter)
        if len(xdata) > 1:
            self.ax.set_xlim(np.amin(xdata), np.amax(xdata))
        self.ax.set_xlabel(self.xtitle)
        self.ax.set_ylabel(self.ytitle)
        self.ax.set_ylim(self.ymin, self.ymax)
        self.ax.set_yticks(np.arange(self.ymin, self.ymax + 1, self.ystep))
        self.canvas.draw()

    def refresh_plot(self) -> None:
        x = self.artist.get_xdata(orig=True)
        y = self.artist.get_ydata(orig=True)
        self.update_plot(x, y)

    def auto_scale(self) -> None:
        y = self.artist.get_ydata(orig=True)
        if len(y) <= 1:
            return
        min = np.floor(np.amin(y))
        max = np.ceil(np.amax(y))
        step = np.round((max - min) / 4)
        self.set_scale(min, max, step)

    def set_scale_min(self, min: float) -> None:
        self.ymin = min
        self.refresh_plot()

    def set_scale_max(self, max: float) -> None:
        self.ymax = max
        self.refresh_plot()

    def set_scale_step(self, step: float) -> None:
        self.ystep = step
        self.refresh_plot()

    def set_scale(self, min: float, max: float, step: float) -> None:
        self.ymin = min
        self.ymax = max
        self.ystep = step
        self.refresh_plot()

    def set_xtitle(self, text: str) -> None:
        self.xtitle = text

    def set_ytitle(self, text: str) -> None:
        self.ytitle = text


class MplPolarWidget(MplWidget):
    def __init__(self, color: str, parent=None):
        super(MplPolarWidget, self).__init__(color, parent)

        self._ticks = True
        # Semi-sensible defaults
        self.rmin = -30.0
        self.rmax = 0.0
        self.rstep = 10.0

        self.ax = self.canvas.fig.add_subplot(projection='polar')
        self.ax.set_theta_zero_location('N')
        self.ax.set_thetagrids(np.arange(0, 360, 30))
        self.artist, *_ = self.ax.plot(np.array([0]), np.array([0]), color=self.color)
        self.canvas.draw()

    @property
    def ticks(self) -> bool:
        return self._ticks

    @ticks.setter
    def ticks(self, setting: bool) -> None:
        self._ticks = setting

    def update_plot(self, xdata: np.ndarray, ydata: np.ndarray) -> None:
        self.ax.cla()
        self.artist, *_ = self.ax.plot(xdata, ydata, color=self.color)
        if not self.ticks:
            self.ax.set_xticklabels([])
            self.ax.set_yticklabels([])
        self.ax.grid(self.grid)
        self.ax.set_theta_zero_location('N')
        self.ax.set_xticks(np.deg2rad(np.arange(-180, 180, 30)))
        self.ax.set_thetalim(-np.pi, np.pi)
        self.ax.set_rlim(self.rmin, self.rmax)
        self.ax.set_rticks(np.arange(self.rmin, self.rmax + 1, self.rstep))
        self.canvas.draw()

    def refresh_plot(self) -> None:
        x = self.artist.get_xdata(orig=True)
        y = self.artist.get_ydata(orig=True)
        self.update_plot(x, y)

    def auto_scale(self) -> None:
        y = self.artist.get_ydata(orig=True)
        if len(y) <= 1:
            return
        min = np.floor(np.amin(y))
        max = np.ceil(np.amax(y))
        step = np.round((max - min) / 4)
        self.set_scale(min, max, step)

    def set_scale_min(self, min: float) -> None:
        self.rmin = min
        self.refresh_plot()

    def set_scale_max(self, max: float) -> None:
        self.rmax = max
        self.refresh_plot()

    def set_scale_step(self, step: float) -> None:
        self.rstep = step
        self.refresh_plot()

    def set_scale(self, min: float, max: float, step: float) -> None:
        self.rmin = min
        self.rmax = max
        self.rstep = step if not np.isclose(step, 0.0) else 1.0
        self.refresh_plot()
