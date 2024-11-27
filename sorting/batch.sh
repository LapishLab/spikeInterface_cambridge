#!/bin/bash

#Load modules
module load miniconda
module load singularity/3.8.3
module load cudatoolkit/11.7
module load apptainer/1.1.8

#Start conda environment
conda activate si_env

#Run the specified script in parallel passing a SLURM array number each time
srun python $1 $SLURM_ARRAY_TASK_ID
