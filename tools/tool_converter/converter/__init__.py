import tkinter as tk
import tkinter.messagebox as messagebox
import h5py
from vtl_common.workspace_manager import Workspace
from vtl_common.localization import get_locale
from .filelist import Filelist
from .form import ConverterForm
from vtl_common.common_GUI.tk_forms import TkDictForm
from .converter_parallel import ConverterParallel

MDATA_WORKSPACE = Workspace("merged_data")
UNPROCESSED_DATA_WORKSPACE = Workspace("unprocessed_data")


class Converter(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master, highlightthickness=1)
        self.config(highlightbackground = "black", highlightcolor= "black")
        self.controller = controller
        tk.Label(self, text=get_locale("mat_converter.title"), font='TkDefaultFont 10 bold') \
            .pack(side="top", fill="x")
        self.file_list = Filelist(self, UNPROCESSED_DATA_WORKSPACE)
        self.file_list.pack(side="left", fill="both", expand=True)
        rpanel = tk.Frame(self)
        rpanel.pack(side="right", fill="y")
        self.form_parser = ConverterForm()
        self.form = TkDictForm(rpanel, self.form_parser.get_configuration_root(), False)
        self.form.pack(side="top", fill="x", expand=True, anchor="nw")
        convert_btn = tk.Button(rpanel, text=get_locale("mat_converter.btn.convert"), command=self.on_convert)
        convert_btn.pack(side="bottom", fill="x", anchor="sw")

    def on_convert(self):
        files = self.file_list.get_files()
        if not files:
            return
        filename = MDATA_WORKSPACE.asksaveasfilename(title=get_locale("mat_converter.filedialog.export.title"),
                                                     filetypes=[(get_locale("app.filedialog_formats.processed_mat"),
                                                                 "*.h5 *.mat")],
                                                     initialdir=".",
                                                     parent=self)
        if not filename:
            return

        self.controller.close_mat_file()  # In case we overwrite it
        conv_parameters = self.form.get_values()
        self.form_parser.parse_formdata(conv_parameters)
        conv_parameters = self.form_parser.get_data()
        return ConverterParallel(self, filelist=files, conv_parameters=conv_parameters, output_filename=filename)