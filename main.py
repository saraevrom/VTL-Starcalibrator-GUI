import tkinter as tk
from tkinter import ttk

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Определение ориентации")

    view_panel = ttk.Frame(root)
    view_panel.grid(row=0,column=0)

    control_panel = ttk.Frame(root)
    control_panel.grid(row=0, column=1)

    topmenu = tk.Menu(root)

    filemenu = tk.Menu(topmenu, tearoff=0)
    topmenu.add_cascade(label="Файл", menu=filemenu)

    root.config(menu=topmenu)
    root.mainloop()