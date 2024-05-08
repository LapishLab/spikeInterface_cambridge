#!/bin/bash

#SBATCH -J testSpikeInterfaceJob
#SBATCH -p gpu-debug
#SBATCH -A r00229
#SBATCH -o testSpikeInterfaceJob_%j.txt
#SBATCH -e testSpikeInterfaceJob_%j.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=nmtimme@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=1
#SBATCH --mem=128GB
#SBATCH --time=01:00:00

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
srun python cambridgeEphysTest1.py