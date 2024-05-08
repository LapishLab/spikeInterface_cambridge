# This script is designed to spike sort open ephys recordings made using Cambridge probes. 
# It is meant to work with spikeSortCambridgeDataJob.sh to submit multiple data sets to 
# independent jobs.
#
# Version History
# 0.1: Developmental version created by Nick Timme in August, 2023.

# Import necessary pieces of software
import spikeinterface.full as si
import probeinterface as pi
from probeinterface import Probe
from probeinterface.plotting import plot_probe
print(si.__version__)

import numpy as np
import matplotlib.pyplot as plt
import csv as csv
import pathlib
import sys
import shutil
import os
# from pathlib import Path

# Get the task ID
taskID = int(sys.argv[1])
# taskID = 1
print('Task ID:',taskID)

# Load the data set list
f = open('/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/cambridgeRecordings.txt', 'r')
csvreader = csv.reader(f, delimiter=',')
dataSetList =[]
for row in csvreader:
    dataSetList.append(row)
f.close()

# Set the open ephys folder path, data set name, channel map, and the location of the spike sorted data for this data set
openephys_folder = dataSetList[taskID - 1][0]
channelMapFile = dataSetList[taskID - 1][1]
path = pathlib.PurePath(openephys_folder)
dataSetName = path.name
spikeSortedDataFolder = '/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/CambridgeProbeSpikeSortingResults/' + dataSetName
spikeSortTempFolder = '/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/CambridgeProbeSpikeSortingResults/' + dataSetName + '/temp'

print('Processing Data Set:',dataSetName)
print('Channel Map Name:',channelMapFile)

# Load the channel map
f = open('/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/CambridgeProbeChannelMapFiles/' + channelMapFile + '.txt', 'r')
reader = f.readlines()
channelMapFileData = []
for row in reader:
    channelMapFileData.append(row)
f.close()
probeName = channelMapFileData[0].strip()
nChannels = len(channelMapFileData) - 1
print('nChannels:',nChannels)
device_channel_indices = np.arange(nChannels)
for i in np.arange(1,nChannels + 1):
    device_channel_indices[i - 1] = int(channelMapFileData[i]) - 1
print('Probe Name:',probeName)
print('device_channel_indices:',device_channel_indices)

# Read the ephys data (stream names are 'Signals AUX', 'Signals CH', 'Signals ADC')
raw_rec = si.read_openephys(openephys_folder,stream_name='Signals CH')
print('raw_rec',raw_rec)

# Create the probe, modify it, and install it with the recording
probe = pi.get_probe(manufacturer='cambridgeneurotech', probe_name=probeName)
probe.set_device_channel_indices(device_channel_indices)
raw_rec.set_probe(probe, in_place=True, group_mode="by_shank")
print('Probe:',probe)

# Plot the probe, if desired
plot_probe(probe,with_device_index=True,with_channel_index=True)
# plt.show() # Uncomment to show plot

# High-pass filter the data
rec1 = si.highpass_filter(raw_rec, freq_min=300.)

# Show the noise histogram
noise_levels_microV = si.get_noise_levels(rec1, return_scaled=True)
noise_levels_int16 = si.get_noise_levels(rec1, return_scaled=False)
fig, ax = plt.subplots()
_ = ax.hist(noise_levels_microV, bins=np.arange(5, 30, 2.5))
ax.set_xlabel('noise  [microV]')

# Identify bad channels and remove them
bad_channel_ids, channel_labels = si.detect_bad_channels(rec1,method="std",std_mad_threshold=3)
rec2 = rec1.remove_channels(bad_channel_ids)
print('bad_channel_ids', bad_channel_ids)

# Show the noise histogram
noise_levels_microV = si.get_noise_levels(rec2, return_scaled=True)
noise_levels_int16 = si.get_noise_levels(rec2, return_scaled=False)
fig, ax = plt.subplots()
_ = ax.hist(noise_levels_microV, bins=np.arange(5, 30, 2.5))
ax.set_xlabel('noise  [microV]')

# Common median reference the data
rec3 = si.common_reference(rec2, operator="median", reference="global")
print('rec',rec3)

# Show the noise histogram
noise_levels_microV = si.get_noise_levels(rec3, return_scaled=True)
noise_levels_int16 = si.get_noise_levels(rec3, return_scaled=False)
fig, ax = plt.subplots()
_ = ax.hist(noise_levels_microV, bins=np.arange(5, 30, 2.5))
ax.set_xlabel('noise  [microV]')
# plt.show() # Uncomment to show plot

# Look at some example traces
fig, ax = plt.subplots(figsize=(20, 10))
some_chans = rec3.channel_ids[[5, 10, 20, ]]
si.plot_timeseries({'filter':rec1, 'cmr': rec3}, backend='matplotlib', mode='line', ax=ax, channel_ids=some_chans)
# plt.show() # Uncomment to show plot

# Get the kilosort3 parameters
KS3Params = si.get_default_sorter_params('kilosort3')
print('KS3Params:',KS3Params)

# Turn off drift correction
KS3Params = {'do_correction': False}

# Increase the NT parameter to avoid EIG did not converge errors
KS3Params = {'NT': 512000}

# # Print recording properties
# print('Recording properties:',rec.get_property_keys())

# # Run the spike sorting with each shank sorted separately (does not work with kilosort3 for shanks with ~12 or fewer channels)
# sorting = si.run_sorter_by_property('kilosort3', rec3, grouping_property='group', working_folder=spikeSortTempFolder, singularity_image="spikeinterface/kilosort3-compiled-base:latest", verbose=True, **KS3Params)

# Run the spike sorting
sorting = si.run_sorter('kilosort3', rec3, output_folder=spikeSortTempFolder, singularity_image="spikeinterface/kilosort3-compiled-base:latest", verbose=True, **KS3Params)

# # Get the kilosort3 parameters
# KS2_5Params = si.get_default_sorter_params('kilosort2_5')
# print('KS2_5Params:',KS2_5Params)

# # Turn off drift correction
# KS2_5Params = {'do_correction': False}

# # Increase the NT parameter to avoid EIG did not converge errors
# KS2_5Params = {'NT': 512000}

# # Remove the block processing (see https://github.com/MouseLand/Kilosort/issues/519)
# KS2_5Params = {'nblocks': 1}

# # Increase the ntbuff parameter to avoid gpuArray errors
# KS2_5Params = {'ntbuff': 256}

# # Run the spike sorting
# sorting = si.run_sorter('kilosort2_5', rec3, output_folder=spikeSortTempFolder, singularity_image="spikeinterface/kilosort2_5-compiled-base:latest", verbose=True, **KS2_5Params)


# Copy the data out of the temporary folder
shutil.copytree(os.path.join(spikeSortTempFolder,'sorter_output'),os.path.join(spikeSortedDataFolder,'sorter_output'))
shutil.copytree(os.path.join(spikeSortTempFolder,'in_container_sorting'),os.path.join(spikeSortedDataFolder,'in_container_sorting'))
shutil.copy(os.path.join(spikeSortTempFolder,'spikeinterface_log.json'),os.path.join(spikeSortedDataFolder,'spikeinterface_log.json'))
shutil.copy(os.path.join(spikeSortTempFolder,'spikeinterface_params.json'),os.path.join(spikeSortedDataFolder,'spikeinterface_params.json'))
shutil.copy(os.path.join(spikeSortTempFolder,'spikeinterface_recording.json'),os.path.join(spikeSortedDataFolder,'spikeinterface_recording.json'))
shutil.rmtree(spikeSortTempFolder)

# Tell user where the data are located
print('Spike Sorted Data:',spikeSortedDataFolder)













