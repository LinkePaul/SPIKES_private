"""This module contains the Graph class, which is used to create and update a matplotlib figure of the spectrum analyzer data.
"""
import colorsys
import warnings
import numpy as np
from typing import Self
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import backend

import styling_options

class Graph:
    def __init__(self, parent: Self) -> None:
        """Initializes the Graph class and creates a matplotlib figure.

        :param parent: Parent widget for the matplotlib figure.
        :type parent: Self
        
        :return: None
        """
        self.parent = parent
        self.trace_num = 0
        self.fig, self.ax, self.canvas = self.create_plot()
        self.lines = []
        self.plot_line = styling_options.color_scheme.get('plot_line0')
        
    def create_plot(self) -> tuple[Figure, Axes, FigureCanvasTkAgg]:
        """Creates an initial matplotlib object.
        
        :return: matplotlib classes Figure, Axes and Canvas instances.
        :rtype: tuple[Figure, Axes, FigureCanvasTkAgg]
        """
        dpi_count = 300
        text_grid = styling_options.color_scheme.get('text_color')
        face_color = styling_options.color_scheme.get('face_color')
        self.plot_line = styling_options.color_scheme.get('plot_line0')
        
        y_lim=(-60, -50)

        warnings.simplefilter("ignore", UserWarning)
        
        fig = Figure(figsize=(10, 5), dpi=dpi_count, constrained_layout=True)
        ax = fig.add_subplot()
        fig.tight_layout(rect=(0.03, 0.03, 0.99, 0.985))

        ax.set_ylim(y_lim[0], y_lim[1])

        ax.grid(True, which='both', linestyle='--', linewidth=0.3, color=text_grid, alpha=0.6)

        fig.patch.set_facecolor(face_color)
        ax.set_facecolor(face_color)

        ax.tick_params(axis='x', colors=text_grid, width=0.5, labelsize=8)
        ax.tick_params(axis='y', colors=text_grid, width=0.5, labelsize=8)
        ax.xaxis.label.set_color(text_grid)
        ax.yaxis.label.set_color(text_grid)
        for spine in ax.spines.values():
            spine.set_color(text_grid)
            spine.set_linewidth(0.4)
        ax.get_xaxis().get_offset_text().set_visible(False)
        ax.get_yaxis().get_offset_text().set_visible(False)

        ax.text(0.99, 0.01, "MHz", transform=ax.transAxes,
                        fontsize=9, color=text_grid, ha='right')
        ax.text(0.01, 0.99, "dBm", transform=ax.transAxes,
                        fontsize=9, color=text_grid, va='top')
    
        canvas = FigureCanvasTkAgg(fig, master=self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, side='top')
        
        return fig, ax, canvas
    
    def update_plot(self, trace: np.ndarray, clear: bool=False, line_num: int=None) -> None:
        """Updates the matplotlib figure with the given trace data.

        :param trace: Trace data to be plotted.
        :type trace: np.ndarray
        
        :param clear: Clears old plotlines, defaults to False
        :type clear: bool, optional
        
        :param line_num: Line number to be updated, defaults to None
        :type line_num: int, optional
        
        :return: None
        """
        if trace is None or line_num is None:
         
            y_min_old = self.ax.get_ylim()[0]
            y_max_old = self.ax.get_ylim()[1]
    
            if self.lines:
                lines = self.lines

            for line in lines:
                data = line.get_data()
                if len(data[1]) != 0:
                    min = round(data[1].min()-7.5)
                    if min < y_min_old:
                        y_min_set = min
                    else:
                        y_min_set = y_min_old
                    
                    max = round(data[1].max()+7.5)
                    if max > y_max_old:
                        y_max_set = max
                    else:
                        y_max_set = y_max_old
            
            self.ax.set_ylim(y_min_set, y_max_set)       
            
            self.canvas.draw()
            return
        
        while len(self.lines) <= line_num:
            color = self.color_picker(int(self.trace_num))
            alpha = 0.95
            line, = self.ax.plot([], [], color=color, linewidth=0.15, alpha=alpha)
            self.lines.append(line)
        
        if clear:
            self.lines[line_num].set_data(trace[:, 0] * 1e-6, trace[:, 1])
            self.ax.relim()
            self.ax.autoscale_view(scaley=False)
            self.trace_num = len(self.lines)
            
        else:
            self.ax.plot(trace[:, 0] * 1e-6, 
                    trace[:, 1], 
                    color=self.color_picker(int(self.trace_num)), 
                    linewidth=0.1
                    )
            self.trace_num += 1
        
        self.canvas.draw()
        
    def clear_plot(self) -> None:
        """Clears the matplotlib figure and draws a blank canvas.
        """
        for line_n in range(len(self.lines)):
            self.lines[line_n].set_data([], [])
        backend.l = 0    
        self.ax.set_ylim(-60, -50)
        self.canvas.draw()
        
    def color_picker(self, its: int, target: int=10, h_range: tuple=(0.667, 1.127)) -> tuple:
        """Returns a color based on the given line/trace number.

        :param its: Line/trace number.
        :type its: int
        
        :param target: Total number of lines/traces until specified end of color range, defaults to 10
        :type target: int, optional
        
        :param h_range: color range in hue format, defaults to (0.667, 1.127)
        :type h_range: tuple, optional
        
        :return: RGB color tuple.
        :rtype: tuple
        """
        h_sum = h_range[1] - h_range[0]
        
        h = ((h_sum/target)*(-its))+h_range[1]
        s = 1.0
        l = 0.65
        rgb = colorsys.hls_to_rgb(h, l, s)
        return rgb
