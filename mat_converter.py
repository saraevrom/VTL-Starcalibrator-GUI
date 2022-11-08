import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as filedialog

class MatConverter(tk.Toplevel):
    def __init__(self, master):
        super(MatConverter, self).__init__(master)
        self.title("Преобразователь mat файлов")
        self.file_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE)
        self.file_listbox.grid(row=0, column=0, sticky="nsew", columnspan=2)
        tk.Button(self, command=self.on_add_file, text="Добавить").grid(row=1, column=0, sticky="nsew")
        tk.Button(self, command=self.on_remove_file, text="Убрать").grid(row=1, column=1, sticky="nsew")

        right_panel = tk.Frame(self)
        right_panel.grid(row=0, column=2, sticky="nsew", rowspan=2)

        self.output_file = tk.StringVar(right_panel)
        tk.Label(right_panel, textvariable=self.output_file).grid(row=0, column=0, sticky="ew")
        tk.Button(right_panel, command=self.on_output_file_select, text="Выбрать имя файла для экспорта")\
            .grid(row=0, column=1, sticky="ew")
        self.average_window = tk.StringVar(right_panel)
        self.average_window.set("1000")
        tk.Label(right_panel, text="Усреднение").grid(row=1, column=0, sticky="ew")
        tk.Entry(right_panel, textvariable=self.average_window).grid(row=1, column=1, sticky="ew")
        tk.Button(right_panel, command=self.on_convert, text="Конвертировать")\
            .grid(row=2, column=0, sticky="ew", columnspan=2)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)


    def on_add_file(self):
        filenames = filedialog.askopenfilenames(title="Импорт данных",
                                                filetypes=[("Файл с сырыми данными", "*.mat *.hdf")])
        if filenames:
            for filename in filenames:
                if filename not in self.file_listbox.get(0,tk.END):
                    self.file_listbox.insert(tk.END,filename)

    def on_remove_file(self):
        cursel = self.file_listbox.curselection()
        print(cursel)
        for i in cursel[::-1]:
                self.file_listbox.delete(i)

    def on_output_file_select(self):
        filename = filedialog.asksaveasfilename(title="Экспорт",
                                                filetypes=[("Файл с упрощёными данными", "*.mat *.hdf")])
        if filename:
            self.output_file.set(filename)

    def on_convert(self):
        pass

if __name__=="__main__":
    root = tk.Tk()
    conv = MatConverter(root)
    root.mainloop()