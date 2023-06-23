import tkinter as tk
from tools.tool_base import ToolBase
from vtl_common.common_GUI.button_panel import ButtonPanel
from vtl_common.workspace_manager import Workspace
from vtl_common.localization import get_locale
from inner_communication import run_script

WORKSPACE_SCRIPTS = Workspace("automation_scripts")

class ToolAutomation(ToolBase):
    def __init__(self, master):
        super().__init__(master)
        self.text = tk.Text(self)
        self.text.pack(side="left",fill="both",expand=True)
        self.buttons = ButtonPanel(self)
        self.buttons.add_button(get_locale("automation.load"),self.on_load,0)
        self.buttons.add_button(get_locale("automation.save"),self.on_save,1)
        self.buttons.add_button(get_locale("automation.run"),self.on_run,2)
        self.buttons.pack(side="right", anchor="ne")

    def on_load(self):
        filename = WORKSPACE_SCRIPTS.askopenfilename(auto_formats=["py"])
        if filename:
            with open(filename,"r") as fp:
                content = fp.read()
            self.text.delete("1.0", tk.END)
            self.text.insert(tk.END, content)

    def on_save(self):
        filename = WORKSPACE_SCRIPTS.asksaveasfilename(auto_formats=["py"])
        if filename:
            content = self.text.get("1.0", tk.END)
            with open(filename, "w") as fp:
                fp.write(content)

    def on_run(self):
        run_script(self.text.get("1.0", tk.END), self.file)