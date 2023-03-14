import tkinter as tk

class ButtonPanel(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.command_rows = []
        self.columnconfigure(0, weight=1)

    def _allocate_rows(self, rows):
        while rows > len(self.command_rows):
            index = len(self.command_rows)
            new_row = tk.Frame(self, bg="red")
            new_row.grid(row=index, column=0, sticky="nsew")
            self.rowconfigure(index, weight=1)
            self.command_rows.append([new_row, 0])

    def add_button(self, text, command, row):
        self._allocate_rows(row+1)
        print(self.command_rows)
        frame, btn_count = self.command_rows[row]
        button = tk.Button(frame, text=text, command=command)
        button.grid(row=0, column=btn_count, sticky="ew")
        frame.columnconfigure(btn_count, weight=1)
        self.command_rows[row][1] += 1
