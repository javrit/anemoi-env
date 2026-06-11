# anemoi-env

This repository contains the environment and scripts for training, finetuning, and running inference with the Météo-France data-driven weather model.

---

## Repository structure

```
anemoi-env/
├── create-datasets/       # Scripts and configs to build Zarr datasets from GRIB outputs
├── forecast-inference/    # Configs and scripts to run ensemble inference
├── pyproject.toml         # Environment dependencies
├── uv.lock
└── README.md
```

---

## Workflows

### 1. Training, finetuning, SDEdit inference

For standard training, finetuning, and SDEdit inference, work directly from the root of this repository:

```bash
cd /path/to/anemoi-env/
```

From here you can:

```bash
# Training
puv run anemoi-training train --config-name=your_config.yaml --config-dir path/to/config/dir/anemoi-training

# SDEdit inference
puv run anemoi-inference run your_inference_config.yaml
```

See the READMEs in `create-datasets/` and `forecast-inference/` for more advanced workflows.

---

### 2. Ensemble inference with enriched initial conditions

This workflow generates an ensemble of forecasts using 35 PEARPEGE members as global forcing. For each member, inference is run individually to build the full ensemble. The LAM initial conditions can be either the standard AROME analysis (giving a 35-member ensemble driven by PEARPEGE perturbations only) or SDEdit-perturbed states (giving a 35×35 ensemble combining both PEARPEGE and SDEdit perturbations).

#### Step 1 — Create the datasets

Move to the `create-datasets/` folder:

```bash
cd create-datasets/
```

Follow the `README` there to:
- Post-process the SDEdit GRIB outputs
- Index the GRIB files
- Build one Zarr dataset per member

#### Step 2 — Run ensemble inference

Move to the `forecast-inference/` folder:

```bash
cd ../forecast-inference/
```

Follow the `README` there to run the ensemble inference for each member.
Outputs are saved as NetCDF files.

#### Step 3 — Convert NetCDF to NumPy for scoring

Return to `create-datasets/`:

```bash
cd ../create-datasets/
```

Run the conversion script to transform the NetCDF outputs into NumPy arrays.
Both the NetCDF files and the NumPy arrays are required to compute scores.
See the `README` in `create-datasets/` for the exact command and arguments.
EOF
