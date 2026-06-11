# SDEdit Dataset Creation Pipeline

This document explains how to create the Zarr datasets used for inference scoring,
starting from raw GRIB outputs of the SDEdit inference.

---

## Overview

The pipeline has 4 steps:

1. Run inference and output GRIB files (one per member per date), to launch from ../ folder.
2. Post-process the GRIB files with `grib_postprocess.py`
3. Index the GRIB files and create one Zarr dataset per member
4. Convert NetCDF inference outputs to NumPy for scoring with `netcdf_to_numpy`

---

## Output structure

```
dataset_folder/
└── member_i/
    ├── grib_index_member_i.db     # GRIB index file
    └── dataset_member_i.zarr      # Zarr dataset
```

---

## Step 1 — Run SDEdit inference

Run the inference for each member to produce GRIB files. Each GRIB file corresponds
to one member for a given date. See the ../ README for details.

---

## Step 2 — Post-process the GRIB files

Use `grib_postprocess.py` to prepare the GRIB files for dataset creation.
This script removes the intermediate +6h step, shifts the remaining steps to +0h
and +6h, and renames the files with `date + 1 day`.

```bash
python grib_postprocess.py
```

Edit the `INPUT_GLOB` and `OUTPUT_DIR` variables at the top of the script before running.

---

## Step 3 — Create the Zarr datasets

### 3a. Index the GRIB files

For each member, create a GRIB index database pointing to the processed GRIB files.
Replace `membre_i` and `_i` with the member number:

```bash
puv run anemoi-datasets grib-index \
    --index /path/to/dataset/membre_i/database_i.db \
    /path/to/processed/gribs/ \
    --match '*_i.grib'
```

Example for member 0:
```bash
puv run anemoi-datasets grib-index \
    --index /project/home/p200177/DE_371/angeliquebonamy/anemoi/inferences/dataset_SDEDIT_102024/membre0/database_0.db \
    /project/home/p200177/DE_371/avritj/experiments_anemoi/inference/grib/processed \
    --match '*_0.grib'
```

### 3b. Create the Zarr datasets (SLURM job array)

The Zarr datasets are created in parallel for all 35 members using a SLURM job array.

The SLURM script uses a template config YAML and patches the member-specific paths
(index DB path) for each member via `sed`. The config template is
`dataset_arome_ia_sdedit_<nb>.yaml`.

A slurm example is available at :

```
slurm_example.sh
```

The slurm used for our experiments is available at :

```
slurm_used.sh
```


This slurm uses a config available at :

```
config_example.sh
```

The config used for our experiments is available at :

```
config_used.sh
```

> **Note on missing dates:** Only the 00h and 18h steps are available in the SDEdit
> outputs (the 06h and 12h steps are missing by construction). These must be
> explicitly listed under `dates.missing`.

---

# AFTER inference : Netcdf to numpy

Once inference with the data-driver forecast model is complete and results are saved as NetCDF files, convert them to
NumPy arrays for scoring using `netcdf_to_numpy.py`.

Edit the following parameters: 

`VARS` :  variables to keep in the numpy file  (default : ["10u", "10v", "2t", "tp"] for scoring)
`DATE_START` : start date of the selected files (default : "2024-10-01")
`DATE_END` : end date of the selected files (default : "2024-10-31")
`DIR_NETCDF` : output dir (default : "/project/home/p200177/DE_371/avritj/anemoi/inf_aromeia")

