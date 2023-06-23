# Scripted automation
Sometimes when you need some conveyor-like behaviour you can create dedicated python script for automated file processing.

## NOTE!
All load_* commands use corresponding workspace
## Included methods:
load_file(filename) -- opens file from merged_data workspace
load_file_raw(filename) -- opens file from unprocessed_data workspace
load_ff(filename) -- opens flat fielding parameters
load_markup_parameters(filename) -- load markup parameters
load_markup_ann(filename) -- load markup neural network
markup_mark_broken(i,j) -- mark pixel as broken in markup
markup_auto() -- make one auto markup iteration. Returns true if another one is possible.
view_frame(frame=None) -- set frame in viewer if provided, returns resulting frame
view_save(frame) -- save selected frame in viewer
