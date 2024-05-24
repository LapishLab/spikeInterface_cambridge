#!/bin/bash

#SBATCH -J spikeSortCambridgeDataJob
#SBATCH -p gpu
#SBATCH -A r00229
#SBATCH -o logs/spikeSortCambridgeDataJob_%j.txt
#SBATCH -e logs/spikeSortCambridgeDataJob_%j.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=daswyga@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --mem=128GB
#SBATCH --time=02:00:00
#SBATCH --array=1-6

#Load modules
module load miniconda/4.12.0
module load singularity/3.8.3
module load cudatoolkit/11.7
module load apptainer/1.1.8

#Start conda environment
conda activate si_env

#Go to the directory with the script
cd /geode2/home/u050/lapishla/BigRed200/spikeInterfaceVer1

#Run your program
srun python spikeSortCambridgeDataJobScript.py $SLURM_ARRAY_TASK_ID
