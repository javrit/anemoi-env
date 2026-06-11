#!/bin/bash -l
#SBATCH -J DE371_diffusion
#SBATCH -A p200177
#SBATCH -N 1
#SBATCH -p cpu
#SBATCH --cpus-per-task=1
#SBATCH --time=04:00:00
#SBATCH --qos=short
#SBATCH --array=0-34

set -x

module load env/staging/2024.1
module load NVHPC
module load GCC
module load Python/3.11.10-GCCcore-13.3.0
load_puv

export HYDRA_FULL_ERROR=1
export OMP_NUM_THREADS=4
export NCCL_ASYNC_ERROR_HANDLING=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True


nb=$((SLURM_ARRAY_TASK_ID))
DATE="2024-10-02"


# Copie du yaml template et remplacement du path indexdb
sed -e "s|/membre3/|/membre${nb}/|g" \
    -e "s|database_3\.db|database_${nb}.db|g" \
    config_${nb}.yaml > config_${nb}_tmp.yaml

puv run anemoi-datasets config_${nb}_tmp.yaml \
    path/to/dataset/folder/membre${nb}/sdedit_mb${nb}.zarr