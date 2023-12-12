#!/bin/bash
#SBATCH --cpus-per-gpu 2
#SBATCH --gpus=1
#SBATCH -e scripts/.slurm-output/slurm-%j.err
#SBATCH -o scripts/.slurm-output/slurm-%j.out

CONDA_BASE=$(conda info --base)
source $CONDA_BASE/etc/profile.d/conda.sh
conda activate dl-gpt

nvidia-smi
python -c "import torch; print(torch.cuda.device_count())"

python scripts/run_experiment.py --model=3
