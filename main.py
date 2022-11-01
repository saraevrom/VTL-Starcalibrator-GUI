import tkinter as tk
from tkinter import ttk
from plotter import Plotter

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Определение ориентации")

    view_panel = ttk.Frame(root)
    view_panel.grid(row=0,column=0,sticky="nsew")
    plot = Plotter(view_panel)
    plot.pack(fill=tk.BOTH, expand=True)

    control_panel = ttk.Frame(root)
    control_panel.grid(row=0, column=1)

    topmenu = tk.Menu(root)

    filemenu = tk.Menu(topmenu, tearoff=0)
    topmenu.add_cascade(label="Файл", menu=filemenu)

    root.config(menu=topmenu)

    root.rowconfigure(0,weight=1)
    root.columnconfigure(0,weight=1)
    root.mainloop()