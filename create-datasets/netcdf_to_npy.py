"""
nc_to_npy.py
=============
Converts NetCDF inference outputs to NumPy arrays for ensemble scoring.

For each date in [DATE_START, DATE_END], this script:
  - Finds all NetCDF files matching the pattern SDEdit_<date>_*.nc in DIR_NETCDF
    (one file per ensemble member)
  - For each file, reads the variables defined in VARS and pivots the flat
    (lat, lon, value) data into 2D spatial arrays
  - Groups the results by lead time (starting at +6h, incrementing by 6h per time step)
  - Concatenates all members along the first axis to get an array of shape
    (n_members, n_variables, lat, lon)
  - Saves one .npy file per (date, lead time) pair

Configuration
-------------
VARS       : list of variables to extract
DATE_START : first date to process (inclusive)
DATE_END   : last date to process (inclusive)
DIR_NETCDF : directory containing the NetCDF files

Output format
-------------
SDEdit_<date>_<leadtime>.npy  →  shape (n_members, n_variables, n_lat, n_lon)
"""

import xarray as xr
import numpy as np
from tqdm import tqdm
import pandas as pd
import matplotlib.pyplot as plt 
import datetime
from glob import glob 
import os

# CONFIG --------------------------------------------------
 
VARS = ["10u", "10v", "2t", "tp"]
DATE_START = "2024-10-01"
DATE_END = "2024-10-31"
DIR_NETCDF = "/project/home/p200177/DE_371/avritj/anemoi/inf_aromeia"

#----------------------------------------------------------

def transform_nc_to_npy(ds_loaded, time):
    ds = ds_loaded.copy()
    fields = []
    for varname in VARS : 
        
        flat = ds[varname].sel(time=time).values
        lat = ds["latitude"].values
        lon = ds["longitude"].values

        df = pd.DataFrame({
            "lat": np.round(lat, 3),
            "lon": np.round(lon, 3),
            "value": flat
        })
        
        field_2D = df.pivot(index="lat", columns="lon", values="value").copy().to_numpy()
        fields.append(field_2D[np.newaxis, :])
    array = np.concatenate(fields, axis=0)
    return array


dates = pd.date_range(start = DATE_START, end = DATE_END)

for date in tqdm(dates): 
    arrays_by_leadtime = {}
    d = date.date()
    date_str = pd.Timestamp(d).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    files = sorted(glob(os.path.join(DIR_NETCDF, f"SDEdit_{d}_*.nc")))

    for file in files:
        leadtime=6 #TODO : bien mettre lt = 6 et +6 car timestep différent.
        ds = xr.open_dataset(file)
        
        for time in ds.time.values:

            narray = transform_nc_to_npy(ds, time)

            if leadtime not in arrays_by_leadtime:
                arrays_by_leadtime[leadtime] = []
            
            arrays_by_leadtime[leadtime].append(narray[np.newaxis,:])

            leadtime += 6

    for lt in arrays_by_leadtime.keys():
        print('leadtime', lt)

        array_cat = np.concatenate(arrays_by_leadtime[lt], axis=0)
        print("array_cat shape", array_cat.shape)
        np.save(f'/project/home/p200177/DE_371/avritj/anemoi/samples_scoring/samples_SDEdit_15steps/SDEdit_{date_str}_{lt}.npy', array_cat)


