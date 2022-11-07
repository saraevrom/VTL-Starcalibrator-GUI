import tkinter as tk
from tkinter import ttk


class MatConverter(tk.Toplevel):
    def __init__(self, master):
        super(MatConverter, self).__init__(master)
        self.title("Преобразователь mat файлов")

