import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import h5py
import numpy as np
import tqdm

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
                if filename not in self.file_listbox.get(0, tk.END):
                    self.file_listbox.insert(tk.END, filename)
                else:
                    messagebox.showwarning(title="Добавка файла", message=f"Файл {filename} уже в списке")

    def on_remove_file(self):
        cursel = self.file_listbox.curselection()
        print(cursel)
        for i in cursel[::-1]:
                self.file_listbox.delete(i)

    def on_output_file_select(self):
        filename = filedialog.asksaveasfilename(title="Экспорт",
                                                filetypes=[("Файл с упрощёными данными", "*.mat *.hdf")],
                                                initialdir=".")
        if filename:
            self.output_file.set(filename)

    def on_convert(self):
        try:
            average_window = int(self.average_window.get())
        #Average window test
        except ValueError:
            messagebox.showerror(title="Ввод данных",message="Введите число элементов для усреднения")
            return
        if average_window <= 0:
            messagebox.showerror(title="Ввод данных", message="Число элементов для усреднения должно быть натуральным")
            return
        #Filename tests
        output_filename = self.output_file.get()
        input_filenames = self.file_listbox.get(0,tk.END)
        print(input_filenames)
        if not output_filename:
            messagebox.showerror(title="Ввод данных", message="Выберите имя файла для готовых данных")
            return

        if output_filename in input_filenames:
            messagebox.showerror(title="Ввод данных", message="Попытка перезаписать один из входных данных")
            return

        frames = 0
        try:
            for input_filename in input_filenames:
                with h5py.File(input_filename,"r") as input_file:
                    file_len = len(input_file['unixtime_dbl_global'])
                    if file_len != len(input_file["pdm_2d_rot_global"]):
                        print(file_len, len(input_file["pdm_2d_rot_global"]))
                        messagebox.showerror(title="Данные", message=f"Файл {input_filename} повреждён")
                        return
                    subframe = file_len // average_window
                    frames += subframe
        except KeyError:
            messagebox.showerror(title="Ввод данных",
                        message="Во входных файлах есть данные без полей unixtime_dbl_global или pdm_2d_rot_global")
            return

        if messagebox.askyesno(title="Преобразование",
                               message=f"Будет создан файл с {frames} кадрами, хотите продолжить?"):
            with h5py.File(output_filename,"w") as output_file:
                data0 = output_file.create_dataset("data0", (frames, 16, 16), dtype="f8")
                utc_time = output_file.create_dataset("UT0", (frames,), dtype="f8")
                pointer = 0
                for input_filename in input_filenames:
                    with h5py.File(input_filename, "r") as input_file:
                        file_len = len(input_file['unixtime_dbl_global'])
                        for i in tqdm.tqdm(range(0, file_len, average_window)):
                            data0[pointer] = np.mean(input_file["pdm_2d_rot_global"][i:i+average_window])
                            utc_time[pointer] = input_file['unixtime_dbl_global'][i][0]
                            pointer += 1


if __name__=="__main__":
    root = tk.Tk()
    conv = MatConverter(root)
    root.mainloop()