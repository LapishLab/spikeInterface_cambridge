#!/bin/bash

#First input ($1) is path to sortSingleRec.py
#Second input ($2) is path to job folder

#Load modules
module load miniconda
module load cudatoolkit
module load apptainer

#Start conda environment
conda activate si_ks4

#Run the specified script in parallel passing a SLURM array number each time
srun python -u $1 --jobFolder $2 --taskID $SLURM_ARRAY_TASK_ID
