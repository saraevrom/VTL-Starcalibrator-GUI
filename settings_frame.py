import tkinter as tk
from tkinter import ttk

# based on https://gist.github.com/mp035/9f2027c3ef9172264532fcd6262f3b01
class ScrollableFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super(ScrollableFrame, self).__init__(master, *args, **kwargs)
        self.view_canvas = tk.Canvas(self, borderwidth=0)
        self.view_port = ttk.Frame(self.view_canvas)
        self.view_canvas_window = self.view_canvas.create_window((0, 0), window=self.view_port, anchor="nw",
                                                       tags="self.view_port")

        self.vertical_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.view_canvas.yview)
        self.horizontal_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.view_canvas.xview)
        self.view_canvas.configure(yscrollcommand=self.vertical_scrollbar.set,
                                   xscrollcommand=self.horizontal_scrollbar.set)

        self.view_canvas.grid(row=0, column=0, sticky="nsew")
        self.horizontal_scrollbar.grid(row=1, column=0, sticky="nsew")
        self.vertical_scrollbar.grid(row=0, column=1, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # bind an event whenever the size of the viewPort frame changes.
        self.view_port.bind("<Configure>", self.reconfigure_frame)
        # bind an event whenever the size of the canvas frame
        self.reconfigure_frame(None)

    def reconfigure_frame(self, event):
        self.view_canvas.configure(scrollregion=self.view_canvas.bbox("all"))



class SettingFormatError(Exception):
    def __init__(self, setting, action):
        self.failed_setting = setting
        self.failed_action = action
        super(SettingFormatError, self).__init__(f"Error {action} {setting}")


class Setting(tk.Frame):
    def __init__(self, master, setting_key, initial_value):
        super(Setting, self).__init__(master)
        self.setting_key = setting_key
        self.initial_value = initial_value
        self.build_setting(self)
        self.reset()
        self.change_callback = None

    def build_setting(self, frame):
        raise NotImplementedError("Required to use setting")

    def set_value(self, value):
        raise NotImplementedError("Required to write value of setting")

    def get_value(self):
        raise NotImplementedError("Required to read value of setting")

    def die(self,action):
        raise SettingFormatError(self.setting_key,action)

    def reset(self):
        self.set_value(self.initial_value)

    def set_dict_value(self, out_dict):
        out_dict[self.setting_key] = self.get_value()


    def get_dict_value(self, in_dict):
        if self.setting_key in in_dict.keys():
            self.set_value(in_dict[self.setting_key])


class EntryValue(Setting):
    def __init__(self, master, setting_key, initial_value, dtype=str):
        super(EntryValue, self).__init__(master, setting_key, initial_value)
        self.dtype = dtype

    def build_setting(self, frame):
        self.entryvar = tk.StringVar(self)
        self.entryvar.set(str(self.initial_value))
        entry = ttk.Entry(frame, textvariable=self.entryvar)
        entry.pack(fill=tk.BOTH, expand=True)

    def get_value(self):
        val = self.entryvar.get()
        try:
            res = self.dtype(val)
            return res
        except ValueError:
            self.die("reading")

    def set_value(self, value):
        self.entryvar.set(str(value))


class CheckboxValue(Setting):
    def __init__(self, master, setting_key, initial_value):
        super(CheckboxValue, self).__init__(master, setting_key, initial_value)

    def build_setting(self, frame):
        self.entryvar = tk.IntVar(self)
        tk.Checkbutton(frame, text="", variable=self.entryvar).pack(fill=tk.BOTH, expand=True)

    def get_value(self):
        return self.entryvar.get() != 0

    def set_value(self, value):
        self.entryvar.set(int(value))


class RangeDoubleValue(Setting):
    def __init__(self, master, setting_key, initial_value, start, end, step=0.01, fmt="%.2f"):
        self.start = start
        self.end = end
        self.step = step
        self.fmt = fmt
        super(RangeDoubleValue, self).__init__(master, setting_key, initial_value)

    def build_setting(self, frame):
        self.entry_field = ttk.Spinbox(frame, from_=self.start, to=self.end, increment=self.step, format=self.fmt,
                                       wrap=True)
        self.entry_field.pack(fill=tk.BOTH, expand=True)

    def get_value(self):
        return self.entry_field.get()

    def set_value(self, value):
        self.entry_field.set(value)

class SliderRangeDoubleValue(Setting):
    def __init__(self, master, setting_key, initial_value, start, end, fmt="{:.2f}"):
        self.start = start
        self.end = end
        self.fmt = fmt
        super(SliderRangeDoubleValue, self).__init__(master, setting_key, initial_value)

    def build_setting(self, frame):
        self.srcvar = tk.DoubleVar(self)
        self.srcvar.trace("w",self.propagate)
        self.displayvar = tk.StringVar(self)
        self.entry_field = ttk.Scale(frame, from_=self.start, to=self.end, orient=tk.HORIZONTAL,variable=self.srcvar)
        self.entry_field.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(frame, textvariable=self.displayvar, width=5).pack(side=tk.LEFT,fill=tk.BOTH)

    def propagate(self,*args):
        self.displayvar.set(self.fmt.format(self.srcvar.get()))

    def get_value(self):
        return self.entry_field.get()

    def set_value(self, value):
        self.entry_field.set(value)

class SettingMenu(ScrollableFrame):
    def __init__(self, master, *args, **kwargs):
        super(SettingMenu, self).__init__(master, *args, **kwargs)
        self.user_settings = []
        self.columnconfigure(0,weight=1)
        self.separator_count = 0
        self.on_change_callback = None

    def get_new_row(self):
        return len(self.user_settings)+self.separator_count

    def on_change(self):
        if self.on_change_callback:
            self.on_change_callback()

    def add_setting(self, setting_type, setting_key, display_name, initial_value, **kwargs):
        newsetting = setting_type(self.view_port, setting_key, initial_value, **kwargs)
        newsetting.change_callback = self.on_change
        newrow = self.get_new_row()
        self.user_settings.append(newsetting)
        ttk.Label(self.view_port,text=display_name).grid(row=newrow, column=0, sticky="ew")
        newsetting.grid(row=newrow, column=1, sticky="ew")

    def add_separator(self,display_name):
        newrow = self.get_new_row()
        ttk.Label(self.view_port, text=display_name, anchor="center", font='TkDefaultFont 10 bold').\
            grid(row=newrow, column=0, sticky="ew", columnspan=2)
        self.separator_count += 1