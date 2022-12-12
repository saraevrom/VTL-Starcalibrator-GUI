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
## Step 1: convert data
* Press "Tools/Convert mat files". 
* Press button "Add" and select raw data.
* Value "Averaging" determines how many frames will be averaged. For example if raw data has 36000000 frames. If averaging is 1000. Processed data will have only 36000.
* Choose file name of processed data using "Choose export file" button.
* Press "Convert"
* Close Mat convertor

NOTE: opening convertor closes file in main window!

## Step 2: flat fielding.
* Open converted data with "File/Open mat file"
* Press "Tools/Flat fielding"
* Choose range via "Point 1" and "Point 2"
* Set averaging to either 60 or 600
* Setting algorithm to "isotropic_lsq_corr_parallel" is prefered.
* press "OK" to applyy settings
* Press "Calculate coefficients"
* You can draw random pair of pixels using "Draw random pair of pixels"
* Press "Save data" when you is satisfied with results.

