#!/bin/bash

#SBATCH -J cambridgeDataPackageJob
#SBATCH -p general
#SBATCH -A r00229
#SBATCH -o cambridgeDataPackageJob_%j.txt
#SBATCH -e cambridgeDataPackageJob_%j.err
#SBATCH --mail-type=ALL
#SBATCH --mail-user=merwatso@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=64GB
#SBATCH --time=02:00:00
#SBATCH --array=1-51

#Load modules
module load matlab

#Go to the directory with the script
cd /geode2/home/u050/lapishla/BigRed200/spikeInterfaceVer1

#Run your program
matlab < cambridgeDataPackageJobScript.m
