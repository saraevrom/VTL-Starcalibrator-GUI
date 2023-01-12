from plotter import GridPlotter

class DualHighlightingplotter(GridPlotter):
    def __init__(self, master):
        super().__init__(master, enable_scale_configuration=False)
        self.firstselected = None
        self.on_right_click_callback = self.on_rmb_event
        self.on_right_click_callback_outofbounds = self.on_click_elsewhere
        self.on_pair_click_callback = None


    def on_click_elsewhere(self):
        self.clear_highlight()
        self.update_matrix_plot(True)
        self.firstselected = None
        self.draw()

    def on_rmb_event(self, i, j):
        if self.firstselected:
            print("Selected pair:", self.firstselected, (i, j))
            self.on_pair_click_callback(self.firstselected, (i, j))
            self.clear_highlight()
            self.firstselected = None
        else:
            self.highlight_pixel(i,j)
            self.firstselected = (i,j)
        self.update_matrix_plot(True)
        self.draw()

