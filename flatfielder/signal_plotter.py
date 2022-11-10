import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from plotter import Plotter
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.pyplot import Normalize
import colorsys



class SignalPlotter(Plotter):
    def __init__(self, master, *args, **kwargs):
        super(SignalPlotter, self).__init__(master, *args, **kwargs)
        self.axes.grid()
