# Data-Driven Météo-France Model — Inference

This repository allows running inference with the Météo-France data-driven weather forecasting model.

## Overview

The inference can be run in two modes:

- **SDEdit + PEARP (35 members)**: uses perturbed initial conditions from SDEdit as the LAM input, combined with a PEARP member as the global forcing.
- **PEARP + AROME analysis (35 members)**: uses the real AROME analysis as the LAM input, combined with a PEARP member as the global forcing. No change needed on the LAM dataset.

For each member, a separate Zarr dataset covering 1 month is available.

---

## Configuration

Example configurations are available at:

```
./example_inference_arome_analysis.yaml  
./example_inference_sdedit.yaml
```

The key section to modify per member is the `input` block:

```yaml
input:
  cutout:
    - lam_0:
        dataset:
          dataset: /path/to/sdedit/membre_X/dataset_X.zarr   # <-- SDEdit dataset for this member
          rescale:
            q_100:
              scale: 0.1
              offset: 0.0
    - global:
        dataset: /path/to/pearp/membre_X.zarr                 # <-- PEARP member corresponding to this member
```

For the **PEARP + AROME analysis** mode, keep the LAM dataset unchanged (use the standard AROME analysis dataset).

---

The configuration used for our experiments is available at :

```
./config_used_inference.yaml
```


## Running inference

From the current directory:

```bash
puv run anemoi-inference run /path/to/config.yaml
```

---

## Running all 35 members (SLURM job array)

The 35 members can be run efficiently using a SLURM task array, one job per member:

```bash
sbatch --array=0-34 run_inference.sh
```

Each task reads the dataset corresponding to `$SLURM_ARRAY_TASK_ID` and writes its output to a separate file.

An example slurm file is available at :

```
slurm_example.sh
```


The array used for our experiments is available at :

```
./slurm_used.sh
```