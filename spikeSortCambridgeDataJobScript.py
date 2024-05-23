# This script is designed to spike sort open ephys recordings made using Cambridge probes. 
# It is meant to work with spikeSortCambridgeDataJob.sh to submit multiple data sets to 
# independent jobs.
#
# Version History
# 0.1: Developmental version created by Nick Timme in August, 2023.

# Import necessary pieces of software
import spikeinterface.full as si
import probeinterface as pi
print(si.__version__)

import numpy as np
import matplotlib.pyplot as plt
import csv as csv
import pathlib
import shutil
import os

# Get the task ID
#taskID = int(sys.argv[1])
taskID = 1
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
spikeSortTempFolder = spikeSortedDataFolder + '_temp'

print('Processing Data Set:',dataSetName)
print('Channel Map Name:',channelMapFile)

# Load the channel map
f = open('/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/CambridgeProbeChannelMapFiles/' + channelMapFile + '.txt', 'r')
csvreader = csv.reader(f, delimiter=',')
channelMap =[]
for row in csvreader:
    channelMap.append(row)
f.close()

probeNames = channelMap.pop(0)
device_channel_indices = np.array(channelMap).astype(int)
device_channel_indices = device_channel_indices -np.min(device_channel_indices) # TODO check that we are consistent on 0 indexing 
print('device_channel_indices', device_channel_indices)
# Read the ephys data (stream names are 'Signals AUX', 'Signals CH', 'Signals ADC')
fullRec = si.read_openephys(openephys_folder,stream_name='Signals CH')
print('raw_rec',fullRec)

for i in range(len(probeNames)):
    ### Create Probe according to Channel map ###
    probe = pi.get_probe(manufacturer='cambridgeneurotech', probe_name=probeNames[i])
    probe.set_device_channel_indices(device_channel_indices[:,i])
    print(probe)
    #pi.plotting.plot_probe(probe)
    
    ### Pull out recording channels for this probe ###
    first = i*len(device_channel_indices)
    last = first+len(device_channel_indices)
    amp_ids = fullRec.get_channel_ids()
    rec = fullRec.channel_slice(amp_ids[first:last])
    print(rec.get_channel_ids())
    
    ### Apply probe to subset of recording ###
    rec = rec.set_probe(probe, group_mode="by_shank")
    
    # Show location of each recording channel in space
    l = rec.get_channel_locations()
    plt.scatter(l[:,0], l[:,1])

    ### Preprocess data ###
    rec = si.highpass_filter(rec, freq_min=300.)
    
    # Show the noise histogram
    noise = si.get_noise_levels(rec, return_scaled=True)
    fig, ax = plt.subplots()
    _ = ax.hist(noise, bins=np.arange(5, 30, 2.5))
    ax.set_xlabel('noise  [microV]')

    # Identify bad channels and remove them
    bad_channel_ids, channel_labels = si.detect_bad_channels(rec,method="std",std_mad_threshold=3)
    rec = rec.remove_channels(bad_channel_ids)
    print('bad_channel_ids', bad_channel_ids)

    # Common median reference the data
    rec = si.common_reference(rec, operator="median", reference="global")
    print('rec',rec)
    
    ### Spike sort ###
    KS3Params = si.get_default_sorter_params('kilosort3')
    KS3Params = {'do_correction': False} # Turn off drift correction
    KS3Params = {'NT': 512000} # Increase the NT parameter to avoid EIG did not converge errors
    print('KS3Params:',KS3Params)
    
    tempSubFolder = os.path.join(spikeSortTempFolder, probeNames[i])
    si.run_sorter('kilosort3',
                rec,
                output_folder= tempSubFolder,
                singularity_image="spikeinterface/kilosort3-compiled-base:latest",
                verbose=True,
                **KS3Params)

# Look at some example traces
# fig, ax = plt.subplots(figsize=(20, 10))
# some_chans = rec3.channel_ids[[5, 10, 20, ]]
# si.plot_timeseries({'filter':rec1, 'cmr': rec3}, backend='matplotlib', mode='line', ax=ax, channel_ids=some_chans)
# plt.show() # Uncomment to show plot


shutil.rmtree(spikeSortedDataFolder, ignore_errors=True) # delete old version of this folder if present
os.rename(spikeSortTempFolder, spikeSortedDataFolder) # rename folder to final version

# Tell user where the data are located
print('Spike Sorted Data:',spikeSortedDataFolder)