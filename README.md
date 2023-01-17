# VTL-Starcalibrator-GUI
Orientation determining software for VTL telescope
## Current features
* Tuning parameters using data from star catalogues.
* Visualizing stars on focal plane.
* Reducing data obtained from detector.
* Parameters saving and loading.
* (WIP) flat-fielding
## Starting
### (optional) create virtual env
```console
python -m venv venv
source venv/bin/activate
```
### Install requirements
```console
pip install -r requirements.txt
```
## Run program
```console
./main.py
```

# Usage
## Preparation
### Step 1: convert data
* Press "Tools/Convert mat files". 
* Press button "Add" and select raw data.
* Value "Averaging" determines how many frames will be averaged. For example if raw data has 36000000 frames. If averaging is 1000. Processed data will have only 36000.
* Choose file name of processed data using "Choose export file" button.
* Press "Convert"
* Close Mat convertor

NOTE: opening convertor closes file in main window!

### Step 2: flat fielding.
* Open converted data with "File/Open mat file"
* Press "Tools/Flat fielding"
* Choose range via "Point 1" and "Point 2"
* Set averaging to either 60 or 600
* Setting algorithm to "isotropic_lsq_corr_parallel" is preferred.
* press "OK" to apply settings
* Press "Calculate coefficients"
* You can draw random pair of pixels using "Draw random pair of pixels"
* Press "Save data" when you satisfied with results.

## Viewing data
If file is opened in main window you can watch data using "Data Playback" tool.
If you did flat-fielding correctly, this tool will apply it automatically.
There are moving average filter settings for viewing dim tracks.

## Extracting background
Also done when file is opened in main window.
Set up cutoffs, min and max intervals (max interval=0 means start with whole file).
After setup press either "Track visible", either "Track not visible" button.
Then process is straightforward: if you see track, press "Track visible", otherwise press "Track not visible".
Pressing "Image is unclear" will redraw image without advancing.
During the process state can be reset using corresponding button. You will be asked to confirm action.
It is possible to review selected/rejected events by clicking them in listbox.
After pressing buttons intervals will be forced to move to corresponding partition.
When data is fully marked up the message will appear. When you are satisfied with results, press "Save selection" button.
If you are not done, but you want to save progress, you can press "Save selection" button to save progress.
**Pressing "Save selection" button will ask you to choose file name of marked data!**
You can load your progress by opening saved file with "Load selection" button.
