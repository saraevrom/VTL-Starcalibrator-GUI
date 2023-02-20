import tkinter as tk
from localization import get_locale, format_locale
from tkinter import messagebox
import os.path as ospath


def format_path(fpath):
    filename = ospath.basename(fpath)
    parentdir = ospath.dirname(fpath)
    parentname = ospath.basename(parentdir)
    return ospath.join(parentname,filename)

class Filelist(tk.Frame):
    def __init__(self,master,workspace):
        super().__init__(master)
        self.workspace = workspace
        self.file_listbox = tk.Listbox(self, selectmode="extended")
        self.file_listbox.pack(side="top", fill="both", expand=True)
        self.file_list = []
        bottompanel = tk.Frame(self)
        bottompanel.pack(side="bottom", fill="x")
        for i in range(4):
            bottompanel.columnconfigure(i, weight=1)
        tk.Button(bottompanel, command=self.on_add_file, text=get_locale("mat_converter.btn.add"))\
            .grid(row=0, column=0, sticky="nsew")
        tk.Button(bottompanel, command=self.on_remove_file, text=get_locale("mat_converter.btn.remove"))\
            .grid(row=0, column=1, sticky="nsew")
        tk.Button(bottompanel, command=self.on_move_up, text=get_locale("mat_converter.btn.move_up"))\
            .grid(row=0, column=2, sticky="nsew")
        tk.Button(bottompanel, command=self.on_move_down, text=get_locale("mat_converter.btn.move_down"))\
            .grid(row=0, column=3, sticky="nsew")

    def on_add_file(self):
        filenames = self.workspace.askopenfilenames(
            title=get_locale("mat_converter.filedialog.import.title"),
            filetypes=[(get_locale("app.filedialog_formats.raw_mat"), "*.mat *.hdf")],
            parent=self)
        if filenames:
            for filename in filenames:
                if filename not in self.file_list:
                    self.file_listbox.insert(tk.END, format_path(filename))
                    self.file_list.append(filename)
                else:
                    messagebox.showwarning(title=get_locale("mat_converter.messagebox.file_in_list.title"),
                                           message=format_locale(
                        "mat_converter.messagebox.file_in_list", filename=filename
                    ),
                                           parent=self)

    def get_files(self):
        return self.file_list.copy()

    def on_remove_file(self):
        cursel = self.file_listbox.curselection()
        print(cursel)
        for i in cursel[::-1]:
            self.file_listbox.delete(i)
            self.file_list.pop(i)

    def on_move_up(self):
        cursel = self.file_listbox.curselection()
        if cursel[0] == 0:
            self.bell()
            return
        self.file_listbox.select_clear(0, "end")
        for index in range(len(cursel)):
            item = cursel[index]
            prev = self.file_listbox.get(item-1)
            self.file_listbox.delete(item-1)
            self.file_listbox.insert(item, prev)
            self.file_list[item], self.file_list[item-1] = self.file_list[item-1], self.file_list[item]
            self.file_listbox.select_set(item-1)

    def on_move_down(self):
        cursel = self.file_listbox.curselection()
        if cursel[-1] == len(self.file_list)-1:
            self.bell()
            return
        self.file_listbox.select_clear(0, "end")
        for index in reversed(range(len(cursel))):
            item = cursel[index]
            prev = self.file_listbox.get(item)
            self.file_listbox.delete(item)
            self.file_listbox.insert(item+1, prev)
            self.file_list[item], self.file_list[item + 1] = self.file_list[item + 1], self.file_list[item]
            self.file_listbox.select_set(item+1)
