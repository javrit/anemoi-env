#!/bin/bash -l
#SBATCH -J DE371_inference
#SBATCH -A p200177
#SBATCH -N 1
#SBATCH -p gpu
#SBATCH --ntasks-per-node=4
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=16
#SBATCH --time=08:00:00
#SBATCH --qos=default
#SBATCH --array=0

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

for DAY in $(seq -w 01 19); do
    DATE="2024-10-${DAY}"
    srun puv run anemoi-inference run /home/users/u102751/code/anemoi/anemoi-inference/inference_sdedit.yaml \
        "input.cutout[0].lam_0.dataset.dataset='/project/home/p200177/DE_371/avritj/anemoi/dataset_sdedit/membre0/sdedit_15steps_mb${nb}_2024.zarr'" \
        "input.cutout[1].global.dataset='/project/home/p200177/DE_371/datasets/pearp_102024/2024_membres/membre_${nb}/mb${nb}_10_2024.zarr'" \
        "date=${DATE}T00:00:00" \
        "output.extract_lam.output.netcdf.path='/project/home/p200177/DE_371/avritj/anemoi/tests/SDEdit_${DATE}_${nb}.nc'"
done
