#!/bin/bash

#First input ($1) is path to sortSingleRec.py
#Second input ($2) is path to job folder

#Load modules
module load miniconda
#module load singularity/3.8.3
module load cudatoolkit/11.7
module load apptainer/1.1.8

#Start conda environment
conda activate si_env

#Run the specified script in parallel passing a SLURM array number each time
srun python $1 --jobFolder $2 --taskID $SLURM_ARRAY_TASK_ID
