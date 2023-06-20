from vtl_common.localization import get_help, get_locale
import tkinter as tk

ARTICLES = ["datetime_hint", "automation"]


class HelpWindow(tk.Toplevel):
    def __init__(self, master, article):
        super().__init__(master)
        self.title(get_locale(f"app.help.{article}"))
        self.text = tk.Text(self)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.insert(tk.END, get_help(article+".md"))
        self.text.config(state="disabled")



def add_help_menu(app_menu: tk.Menu):
    menu = tk.Menu(app_menu, tearoff=0)
    for article in ARTICLES:
        def wrapper():
            HelpWindow(app_menu.winfo_toplevel(), article)
        menu.add_command(label=get_locale(f"app.help.{article}"), command=wrapper)
    app_menu.add_cascade(label=get_locale("app.menu.help"), menu=menu)