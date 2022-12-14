#!/usr/bin/env python3
#-*-coding:utf8-*-

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import json
import os.path

def get_kwarg(kwdict,key,defval):
    if key in kwdict.keys():
        return kwdict[key]
    else:
        return defval

def get_kw_bool(kwdict,key,defval=False):
    return get_kwarg(kwdict,key,defval)


'''
Creates tkinter input forms based on configuration
'''


class ScrollView(ttk.Frame):
    '''
    Class for scrollable frame view
    Obtained from tutorial at https://blog.teclado.com/tkinter-scrollable-frames/
    '''
    def __init__(self,parent,*args,**kwargs):
        super().__init__(parent,*args,**kwargs)
        self.canvas = tk.Canvas(self)
        self.v_scrollbar = tk.Scrollbar(self,orient="vertical",command = self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self,orient="horizontal",command = self.canvas.xview)


        self.contents = tk.Frame(self.canvas)
        self.contents.bind("<Configure>", self.on_content_change)
        self.drawn_window_id = self.canvas.create_window((0,0), window=self.contents,anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set,xscrollcommand=self.h_scrollbar.set)
        self.h_scrollbar.pack(side="bottom",fill="x")
        self.v_scrollbar.pack(side="right",fill="y")
        self.canvas.pack(side="left",fill="both",expand=True)
        self.canvas.bind("<Configure>", self.on_canvas_change)


    def on_content_change(self,event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_change(self, event):
        width = self.canvas.winfo_width()
        if width>400:
            self.canvas.itemconfig(self.drawn_window_id, width=width)
        else:
            self.canvas.itemconfig(self.drawn_window_id, width=400)


class ConfigEntry(object):
    '''
    Base class for form fields.
    Field can accept configuration dictionary, mentioned as "conf".
    Some keys are common:
    display_name -- field prompt that appears on screen
    default -- default value, oprional

    type -- field type, not required by fields themselves. Instead TkDictForm class uses it to determine field type. it will be mentioned in fields.

    Some keys are unique to fields. See help(<Field type>Entry)
    '''
    def __init__(self,name,master,conf,color_index=0):
        self.conf = conf
        self.name = name
        self.color_index = color_index
        if color_index%2==0:
            color = "#BBBBBB"
        else:
            color = "#DDDDDD"
        self.frame = tk.Frame(master, highlightbackground="gray",background=color, highlightthickness=1,bd=5)

    def get_value(self):
        raise NotImplementedError("This method is not implemented")

    def set_value(self,newval):
        raise NotImplementedError("This method is not implemented")


class EntryInvalidException(Exception):
    '''
    Can occur when processing field result.
    '''
    def __init__(self,fieldname,reason):
        message = "Invalid value encountered at {}, reason: {}".format(fieldname,reason)
        super().__init__(message)
        self.fieldname = fieldname
        self.reason = reason

class StringEntry(ConfigEntry):
    '''
    Enter a string

    type: "str"
    No unique keys
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        tk.Label(self.frame,text=conf["display_name"]).pack(side="left",fill="both")
        self.textvar = tk.StringVar(master)
        tk.Entry(self.frame,textvar=self.textvar).pack(side="left",fill="both")

    def set_value(self,newval):
        self.textvar.set(newval)

    def get_value(self):
        return self.textvar.get()

    def get_frame(self):
        return self.frame

class IntEntry(ConfigEntry):
    '''
    Enter an integer

    type: "int"
    No unique keys
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        tk.Label(self.frame,text=conf["display_name"]).pack(side="left",fill="both")
        self.textvar = tk.StringVar(master)
        tk.Entry(self.frame,textvar=self.textvar).pack(side="left",fill="both")

    def set_value(self,newval):
        self.textvar.set(str(newval))

    def get_value(self):
        sval = self.textvar.get()
        try:
            val = int(sval)
            return val
        except ValueError:
            raise EntryInvalidException(self.name,"Could not convert \"{}\" to integer".format(sval))

class FloatEntry(ConfigEntry):
    '''
    Enter a float

    type: "float"
    No unique keys
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        tk.Label(self.frame,text=conf["display_name"]).pack(side="left",fill="both")
        self.textvar = tk.StringVar(master)
        tk.Entry(self.frame,textvar=self.textvar).pack(side="left",fill="both")

    def set_value(self,newval):
        self.textvar.set(str(newval))

    def get_value(self):
        sval = self.textvar.get()
        try:
            val = float(sval)
            return val
        except ValueError:
            raise EntryInvalidException(self.name,"Could not convert \"{}\" to float".format(sval))

class CheckmarkEntry(ConfigEntry):
    '''
    Enter a string

    type: "bool"
    No unique keys
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        self.intvar = tk.IntVar(master)
        tk.Checkbutton(self.frame,text=conf["display_name"],variable=self.intvar).pack(anchor="nw")

    def set_value(self,newval):
        self.intvar.set(int(newval))

    def get_value(self):
        return bool(self.intvar.get())

class FileEntry(ConfigEntry):
    '''
    Enter a filename. It has "Save file as" behaviour.

    type: "file"
    initialdir -- initial director for file dialog
    filetypes -- File types for dialog
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        self.stringvar = tk.StringVar(master)
        tk.Label(self.frame,text=conf["display_name"]).pack(side="left")
        tk.Button(self.frame,text="Choose file",command=self.command).pack(side="left")
        tk.Label(self.frame,textvar=self.stringvar).pack(side="left",fill="x")

    def command(self):
        pth = filedialog.asksaveasfilename(initialdir=self.conf["initialdir"],filetypes=self.conf["filetypes"])
        if pth:
            self.set_value(pth)
        top = self.frame.winfo_toplevel()
        #top.grab_set()
        top.lift()

    def set_value(self,newval):
        if newval:
            self.stringvar.set(os.path.relpath(newval,self.conf["initialdir"]))
        else:
            self.stringvar.set("")
        self.realvalue = newval

    def get_value(self):
        return self.realvalue

class RadioEntry(ConfigEntry):
    '''
    Choose a string via radio buttons.

    type: "radio"
    values -- selection options.
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        tk.Label(self.frame,text=conf["display_name"]).grid(row=0,column=0)
        self.intvar = tk.IntVar(master)
        self.intvar.set(0)
        ind = 0
        for val in self.conf["values"]:
            tk.Radiobutton(self.frame,text=val,value=ind,variable=self.intvar).grid(row=ind+1,column=1)
            ind+=1

    def set_value(self,newval):
        self.intvar.set(self.conf["values"].index(newval))

    def get_value(self):
        return self.conf["values"][self.intvar.get()]

class ComboEntry(ConfigEntry):
    '''
    Choose a string via combobox.

    type: "combo"
    values -- selection options.
    readonly -- is it possible to edit text inside box?
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        tk.Label(self.frame, text=conf["display_name"]).pack(side="left")
        ro = get_kw_bool(conf, "readonly")
        if ro:
            self.combobox = ttk.Combobox(self.frame, values=conf["values"], state="readonly")
        else:
            self.combobox = ttk.Combobox(self.frame, values=conf["values"])
        self.combobox.pack(side="left")

    def set_value(self, newval):
        self.combobox.set(newval)

    def get_value(self):
        return self.combobox.get()

FIELDTYPES = {
    "str":[StringEntry,False],
    "int":[IntEntry,False],
    "float":[FloatEntry,False],
    "bool":[CheckmarkEntry,False],
    "radio":[RadioEntry,False],
    "file":[FileEntry,False],
    "combo":[ComboEntry,False]
}


def create_field(name,parent,conf, color_index=0):
    field_type,req_default = FIELDTYPES[conf["type"]]
    field = field_type(name,parent,conf, color_index)
    field.frame.pack(side="top",fill="x", expand=True)
    if "default" in conf.keys() or req_default:
        field.set_value(conf["default"])
    return field

class ArrayEntry(ConfigEntry):
    '''
    Creates array of certain field. To add and remove elements use +/- buttons.


    type: "array"
    subconf -- config for containing field. Index is appended to display_name.
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        tk.Label(self.frame,text=conf["display_name"]).pack(side="top", anchor="nw")
        self.subframe = tk.Frame(self.frame)
        self.subframe.pack(side="top",fill="both")
        self.subfields = []
        bottomframe = tk.Frame(self.frame)
        tk.Button(bottomframe,text="-",command=self.delfield).pack(side="right")
        tk.Button(bottomframe,text="+",command=self.addfield).pack(side="left")
        bottomframe.pack(side="bottom",fill="x")

    def addfield(self,value_to_set=None):
        subconf = self.conf["subconf"].copy()
        i = len(self.subfields)
        if "display_name" in subconf.keys():
            subconf["display_name"] = subconf["display_name"] + " " + str(i)
        else:
            subconf["display_name"] = str(i)
        name = "{}[{}]".format(self.name, i)


        field = create_field(name,self.subframe,subconf,self.color_index+1)

        if value_to_set is not None:
            field.set_value(value_to_set)
        self.subfields.append(field)

    def delfield(self):
        if self.subfields:
            last = self.subfields.pop(-1)
            last.frame.destroy()

    def set_value(self,newval):
        self.subfields.clear()
        for widget in self.subframe.winfo_children():
            widget.destroy()
        for e in newval:
            self.addfield(e)


    def get_value(self):
        r = []
        for sf in self.subfields:
            r.append(sf.get_value())
        return r

FIELDTYPES["array"] = [ArrayEntry,False]

class AlternatingEntry(ConfigEntry):
    '''
    Alternating field based on selection.

    type: "alter"
    values -- selection options. Array of dicts
        values[i]["name"] -- Branch name
        values[i]["subconf"] -- Entry config

    Return value is dict with structure:
        r["selection_type"] -- selected branch name
        r["value"] -- contents of branch
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        topframe = tk.Frame(self.frame)
        topframe.pack(side="top",fill="x")

        self.subframe = tk.Frame(self.frame)
        self.subframe.pack(side="bottom",fill="both",expand=True)

        tk.Label(topframe,text=conf["display_name"]).pack(side="left")

        self.valnames = [item["name"] for item in conf["values"]]
        self.subconfs = [item["subconf"] for item in conf["values"]]
        self.subfield = None

        self.sv = tk.StringVar(self.frame)
        self.sv.trace('w',self.on_combo_change)

        self.combobox = ttk.Combobox(topframe,textvar=self.sv,values = self.valnames,state="readonly")
        self.combobox.pack(side="left",fill="x",expand=False)
        #for sc in subconfs:
        #    self.addfield(sc)
        self.last_index=None


    def on_combo_change(self,*args,**kwargs):
        sel = self.sv.get()
        self.select_field(self.valnames.index(sel))

    def select_field(self,index):
        if self.last_index == index:
            return False
        if self.subfield is not None:
            self.subfield.frame.destroy()
            self.subfield = None
        subconf =self.subconfs[index]
        name = "{}[{}]".format(self.name, index)

        if subconf is None:
            field = None
        else:
            field = create_field(name,self.subframe,subconf, self.color_index+1)

        self.subfield=field
        self.last_index=index
        return True


    def set_value(self,newval):
        sel = newval["selection_type"]
        self.combobox.set(sel)
        self.select_field(self.valnames.index(sel))
        if "value"in newval.keys() and (self.subfield is not None):
            self.subfield.set_value(newval["value"])

    def get_value(self):
        stype = self.combobox.get()
        if self.subfield:
            return {"selection_type":stype,"value":self.subfield.get_value()}
        else:
            return {"selection_type":stype,"value": None}

FIELDTYPES["alter"] = [AlternatingEntry,True]

class SubFormEntry(ConfigEntry):
    '''
    Creates small form inside.


    type: "subform"
    subconf -- config for internal form.
    use_scrollview -- should form use scrollable canvas?
    '''
    def __init__(self,name,master,conf,color_index=0):
        super().__init__(name,master,conf,color_index)
        lab = tk.Label(self.frame,text=conf["display_name"], anchor='w')
        lab.pack(side="top",fill="x",expand=True)
        self.subconf = conf["subconf"]
        use_scrollview = True
        if "use_scrollview" in conf.keys():
            use_scrollview = conf["use_scrollview"]
        self.subform = TkDictForm(self.frame,self.subconf,use_scrollview)
        self.subform.pack(side="bottom",fill="x",expand=True,padx=20)

    def set_value(self,newval):
        self.subform.set_values(newval)

    def get_value(self):
        return self.subform.get_values()

FIELDTYPES["subform"] = [SubFormEntry,False]

class TkDictForm(tk.Frame):
    '''
    Tkinter configurable form.

    argiments for __init__:
    master -- master widget for form.
    tk_form_configuration -- configuration. See help(ConfigEntry) for details.
    use_scrollview -- shoud we use scrollable canvas instead of just tkinter frame?
    '''
    def __init__(self,master,tk_form_configuration,use_scrollview=True):
        super(TkDictForm,self).__init__(master)
        self.master = master
        self.tk_form_configuration = tk_form_configuration

        if use_scrollview:
            self.formview = ScrollView(self)
            self.formview.pack(side="top",fill="both",expand=True)
            self.contents_tgt = self.formview.contents
        else:
            self.formview = None
            self.contents_tgt = tk.Frame(self)
            self.contents_tgt.pack(fill="both",expand=True)

        self.fields = dict()
        for i in tk_form_configuration.keys():
            conf = tk_form_configuration[i]
            name = i
            field = create_field(name,self.contents_tgt,conf)
            self.fields[i] = field

    def get_values(self):
        '''
        Get dictionary of field values.
        '''
        res = dict()
        for i in self.tk_form_configuration.keys():
            res[i] = self.fields[i].get_value()
        return res

    def set_values(self,values):
        '''
        Set fields by dictionary of values. Will set only present fields.
        '''
        keys = set(values.keys()).intersection(set(self.fields.keys()))
        #print("Requested values:",list(values.keys()))
        #print("Available values:",list(self.fields.keys()))
        for i in keys:
            self.fields[i].set_value(values[i])

