import spikeinterface.full as si
import probeinterface as pi
print('Spike Interface Version: ',si.__version__)

import numpy as np
import matplotlib.pyplot as plt
import csv as csv
import pathlib
import shutil
import sys
import os
import warnings
import pandas

# Get the task ID

jobfolder = sys.argv[1]
print('job folder', jobfolder)
taskID = int(sys.argv[2])
print('Task ID:', taskID)


# Load the data set list
# f = open('/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/cambridgeRecordings.txt', 'r')
# csvreader = csv.reader(f, delimiter=',')
# dataSetList =[]
# for row in csvreader:
#     dataSetList.append(row)
# f.close()

# # Set the open ephys folder path, data set name, channel map, and the location of the spike sorted data for this data set
# openephys_folder = dataSetList[taskID - 1][0]
# channelMapFile = dataSetList[taskID - 1][1]
# path = pathlib.PurePath(openephys_folder)
# dataSetName = path.name
# spikeSortedDataFolder = '/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/CambridgeProbeSpikeSortingResults/' + dataSetName
# spikeSortTempFolder = spikeSortedDataFolder + '_temp'

# print('Processing Data Set:',dataSetName)
# print('Channel Map Name:',channelMapFile)

# # Load the channel map
# f = open('/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/CambridgeProbeChannelMapFiles/' + channelMapFile + '.txt', 'r')
# csvreader = csv.reader(f, delimiter=',')
# channelMap =[]
# for row in csvreader:
#     channelMap.append(row)
# f.close()

# probeNames = channelMap.pop(0)
# device_channel_indices = np.array(channelMap).astype(int)
# device_channel_indices = device_channel_indices -np.min(device_channel_indices) # TODO check that we are consistent on 0 indexing 
# #print('device_channel_indices', device_channel_indices)
# # Read the ephys data (stream names are 'Signals AUX', 'Signals CH', 'Signals ADC')
# fullRec = si.read_openephys(openephys_folder)

# # Pull out signal channels (IDs starting with CH)
# isSignalChannel = np.char.find(fullRec.channel_ids, 'CH')==0
# signalChannels = fullRec.channel_ids[isSignalChannel]
# fullRec = fullRec.channel_slice(channel_ids=signalChannels)

# #
# print('Signal Recording: ',fullRec)

# if fullRec.get_num_segments() > 1:
#     segmentDuration = [fullRec.get_duration(i) for i in range(fullRec.get_num_segments())]
#     warnings.warn('Raw data contains multiple segments with the following time durations (s):'
#                   + '\n' + str(segmentDuration)
#                   + '\n I will just spike sort the longest segment')
#     fullRec = fullRec.select_segments(int(np.argmax(segmentDuration)))
    
# for i in range(len(probeNames)):
#     ### Create Probe according to Channel map ###
#     probe = pi.get_probe(manufacturer='cambridgeneurotech', probe_name=probeNames[i])
#     probe.set_device_channel_indices(device_channel_indices[:,i])
#     #print(probe)
#     #pi.plotting.plot_probe(probe)
    
#     ### Pull out recording channels for this probe ###
#     first = i*len(device_channel_indices)
#     last = first+len(device_channel_indices)
#     amp_ids = fullRec.get_channel_ids()
#     rec = fullRec.channel_slice(amp_ids[first:last])
#     #print(rec.get_channel_ids())
    
#     ### Apply probe to subset of recording ###
#     rec = rec.set_probe(probe, group_mode="by_shank")
    
#     # Show location of each recording channel in space
#     l = rec.get_channel_locations()
#     plt.scatter(l[:,0], l[:,1])

#     ### Preprocess data ###
#     rec = si.bandpass_filter(recording=rec,freq_min=300.,freq_max=3000.)
    
#     # Show the noise histogram
#     noise = si.get_noise_levels(rec, return_scaled=True)
#     fig, ax = plt.subplots()
#     _ = ax.hist(noise, bins=np.arange(5, 30, 2.5))
#     ax.set_xlabel('noise  [microV]')

#     # Identify bad channels and remove them
#     bad_channel_ids, channel_labels = si.detect_bad_channels(rec,method="std",std_mad_threshold=3)
#     rec = rec.remove_channels(bad_channel_ids)
#     print('bad_channel_ids: ', bad_channel_ids)

#     # Common median reference the data
#     rec = si.common_reference(rec, operator="median", reference="global")
#     #print('rec',rec)
    
#     ### Spike sort ###
#     KS3Params = si.get_default_sorter_params('kilosort3')
#     #KS3Params['do_correction'] = False # Turn off drift correction
#     #KS3Params['NT'] = 512000 # Increase the NT parameter to avoid EIG did not converge errors
#     print('KS3Params:',KS3Params)
    
#     #export SPIKEINTERFACE_DEV_PATH="~/.conda/envs/si_env/lib/python3.9/site-packages/spikeinterface"
    
#     tempSubFolder = os.path.join(spikeSortTempFolder, probeNames[i])
#     sorting = si.run_sorter('kilosort3',
#                 rec,
#                 output_folder= tempSubFolder,
#                 singularity_image="spikeinterface/kilosort3-compiled-base:latest",
#                 verbose=True,
#                 delete_container_files=False,
#                 **KS3Params)
    
#     ### Extract waveforms and compute quality metrics ###
#     try:
#         print('calculating  metrics')
#         waveformFolder = os.path.join(tempSubFolder, 'waveforms')
#         we = si.extract_waveforms(
#             sorting=sorting,
#             recording=rec, 
#             folder=waveformFolder,
#             overwrite=True)
#         metrics = si.compute_quality_metrics(we)
#         metricsFileName = os.path.join(tempSubFolder,'sorter_output','qualityMetrics.csv')
#         metrics.to_csv(metricsFileName)
#     except:
#         warnings.warn('Computing quality metrics failed')


# shutil.rmtree(spikeSortedDataFolder, ignore_errors=True) # delete old version of this folder if present
# os.rename(spikeSortTempFolder, spikeSortedDataFolder) # rename folder to final version

# # Tell user where the data are located
# print('Spike Sorted Data:',spikeSortedDataFolder)
