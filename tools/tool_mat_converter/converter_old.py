import tkinter as tk
import tkinter.messagebox as messagebox
import h5py
import numpy as np
import tqdm
import scipy.io as scipio
from vtl_common.localization import get_locale, format_locale
from tools.tool_base import ToolBase
import os.path as ospath
from .single_copy import average_single_file
from vtl_common.workspace_manager import Workspace

MDATA_WORKSPACE = Workspace("merged_data")
UNPROCESSED_DATA_WORKSPACE = Workspace("unprocessed_data")

class ConverterOld(tk.Frame):
    def __init__(self, master, controller=None):
        super(ConverterOld, self).__init__(master, highlightthickness=1)
        self.config(highlightbackground = "black", highlightcolor= "black")
        if controller is None:
            self.controller = master
        else:
            self.controller = controller

        tk.Label(self, text=get_locale("mat_converter.title"), font='TkDefaultFont 10 bold')\
            .grid(row=0, column=0, columnspan=3, sticky="nsew")

        self.file_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE)
        self.file_list = []
        self.file_listbox.grid(row=1, column=0, sticky="nsew", columnspan=2)
        tk.Button(self, command=self.on_add_file, text=get_locale("mat_converter.btn.add")).grid(row=2, column=0, sticky="nsew")
        tk.Button(self, command=self.on_remove_file, text=get_locale("mat_converter.btn.remove")).grid(row=2, column=1, sticky="nsew")

        right_panel = tk.Frame(self)
        right_panel.grid(row=1, column=2, sticky="nsew", rowspan=2)

        self.output_file = tk.StringVar(right_panel)
        self.full_output_file = ""
        tk.Label(right_panel, textvariable=self.output_file).grid(row=0, column=0, sticky="ew")
        tk.Button(right_panel, command=self.on_output_file_select, text=get_locale("mat_converter.btn.choose_export"))\
            .grid(row=0, column=1, sticky="ew")
        self.average_window = tk.StringVar(right_panel)
        self.average_window.set("1000")

        tk.Label(right_panel, text=get_locale("mat_converter.label.averaging")).grid(row=1, column=0, sticky="ew")
        tk.Entry(right_panel, textvariable=self.average_window).grid(row=1, column=1, sticky="ew")

        self.lcut = tk.StringVar(self)
        self.lcut.set("0")
        self.rcut = tk.StringVar(self)
        self.rcut.set("0")

        tk.Label(right_panel, text=get_locale("mat_converter.label.l_cut")).grid(row=2, column=0, sticky="ew")
        tk.Entry(right_panel, textvariable=self.lcut).grid(row=2, column=1, sticky="ew")

        tk.Label(right_panel, text=get_locale("mat_converter.label.r_cut")).grid(row=3, column=0, sticky="ew")
        tk.Entry(right_panel, textvariable=self.rcut).grid(row=3, column=1, sticky="ew")

        tk.Button(right_panel, command=self.on_convert, text=get_locale("mat_converter.btn.convert"))\
            .grid(row=4, column=0, sticky="ew", columnspan=2)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)


    def on_add_file(self):
        filenames = UNPROCESSED_DATA_WORKSPACE.askopenfilenames(title=get_locale("mat_converter.filedialog.import.title"),
                                                filetypes=[(get_locale("app.filedialog_formats.raw_mat"), "*.mat *.hdf")],
                                                parent=self)
        if filenames:
            for filename in filenames:
                if filename not in self.file_list:
                    self.file_listbox.insert(tk.END, ospath.basename(filename))
                    self.file_list.append(filename)
                else:
                    messagebox.showwarning(title="Добавка файла", message=format_locale(
                                               "mat_converter.messagebox.file_in_list", filename=filename
                                           ),
                                            parent=self)

    def on_remove_file(self):
        cursel = self.file_listbox.curselection()
        print(cursel)
        for i in cursel[::-1]:
                self.file_listbox.delete(i)
                self.file_list.pop(i)

    def on_output_file_select(self):
        filename = MDATA_WORKSPACE.asksaveasfilename(title=get_locale("mat_converter.filedialog.export.title"),
                                                filetypes=[(get_locale("app.filedialog_formats.processed_mat"), "*.mat *.hdf")],
                                                initialdir=".",
                                                 parent=self)
        if filename:
            self.output_file.set(ospath.basename(filename))
            self.full_output_file = filename

    def on_convert(self):
        try:
            average_window = int(self.average_window.get())
            lcut = int(self.lcut.get())
            rcut = int(self.rcut.get())
        #Average window test
        except ValueError:
            messagebox.showerror(title=get_locale("mat_converter.messagebox.input_error.title"),
                                 message=get_locale("mat_converter.messagebox.input_error.msg_average"),
                                 parent=self)
            return
        if average_window <= 0:
            messagebox.showerror(title=get_locale("mat_converter.messagebox.input_error.title"),
                                 message=get_locale("mat_converter.messagebox.input_error.msg_average_negative"),
                                 parent=self)
            return
        #Filename tests
        output_filename = self.full_output_file
        input_filenames = self.file_list[:]
        print(input_filenames)
        if not output_filename:
            messagebox.showerror(title=get_locale("mat_converter.messagebox.input_error.title"),
                                 message=get_locale("mat_converter.messagebox.input_error.missing_export_filename"),
                                 parent=self)
            return

        if output_filename in input_filenames:
            messagebox.showerror(title=get_locale("mat_converter.messagebox.input_error.title"),
                                 message=get_locale("mat_converter.messagebox.input_error.overwrite_attempt"),
                                 parent=self)
            return

        if len(input_filenames) == 1:
            print("Shorten file")
            self.controller.close_mat_file()
            average_single_file(src=input_filenames[0], dst=output_filename,
                                lcut=lcut, rcut=rcut,
                                average_window=average_window)
            return

        frames = 0
        try:
            for input_filename in input_filenames:
                with h5py.File(input_filename,"r") as input_file:
                    file_len = len(input_file['unixtime_dbl_global'])
                    if file_len != len(input_file["pdm_2d_rot_global"]):
                        print(file_len, len(input_file["pdm_2d_rot_global"]))
                        messagebox.showerror(
                            title=get_locale("mat_converter.messagebox.data_error.title"),
                            message=format_locale("mat_converter.messagebox.data_error.damaged_file",
                                                  input_filename=input_filename),
                            parent=self
                        )
                        return
                    subframe = int(np.ceil(file_len / average_window))
                    frames += subframe
        except KeyError:
            messagebox.showerror(title=get_locale("mat_converter.messagebox.input_error.title"),
                        message=get_locale("mat_converter.messagebox.input_error.missing_fields"),
                        parent=self)
            return

        if messagebox.askyesno(title=get_locale("mat_converter.messagebox.conversion.title"),
                               message=format_locale("mat_converter.messagebox.conversion.msg", frames=frames),
                              parent=self):

            self.controller.close_mat_file()  # In case we overwrite it
            with h5py.File(output_filename, "w") as output_file:
                data0 = output_file.create_dataset("data0", (frames, 16, 16), dtype="f8")
                utc_time = output_file.create_dataset("UT0", (frames,), dtype="f8")
                pointer = 0
                for input_filename in input_filenames:
                    with h5py.File(input_filename, "r") as input_file:
                        file_len = len(input_file['unixtime_dbl_global'])
                        if average_window == 1:
                            # Just copy data
                            data0[pointer:pointer+file_len] = input_file["pdm_2d_rot_global"][:]
                            utc_time[pointer:pointer+file_len] = np.array(input_file['unixtime_dbl_global']).T[0]
                            pointer += file_len
                        else:
                            for i in tqdm.tqdm(range(0, file_len, average_window)):
                                data0[pointer] = np.mean(input_file["pdm_2d_rot_global"][i:i+average_window], axis=0)
                                utc_time[pointer] = input_file['unixtime_dbl_global'][i][0]
                                pointer += 1

