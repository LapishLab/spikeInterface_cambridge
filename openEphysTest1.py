# This script is designed to load and spike sort open ephys data recorded with neuropixels.
# It is based on this guide: https://spikeinterface.readthedocs.io/en/latest/how_to/analyse_neuropixels.html

import spikeinterface.full as si
import spikeinterface.widgets as siw
print(si.__version__)

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Define the path to the data
base_folder = Path('/N/project/lapishLabWorkspace/HeadFixedInjectionExp/2023-09-26-Session2')
openephys_folder = base_folder / '2023-09-26_15-26-51'

# Figure out the data streams in this data set
stream_names, stream_ids = si.get_neo_streams('openephys', openephys_folder)
print('stream_names',stream_names)

# Read the data LFP data from probe A (this automatically loads the probe map)
raw_rec = si.read_openephys(openephys_folder, stream_name='Record Node 102#Neuropix-PXI-100.ProbeA-AP')
print('raw_rec',raw_rec)

# Plot the bottom part of the channel map
fig, ax = plt.subplots(figsize=(15, 10))
si.plot_probe_map(raw_rec, ax=ax, with_channel_ids=True)
ax.set_ylim(-100, 100)
# plt.show() # Uncomment to show plot

# High-pass filter the data
rec1 = si.highpass_filter(raw_rec, freq_min=300.)

# Identify bad channels and remove them
bad_channel_ids, channel_labels = si.detect_bad_channels(rec1)
rec2 = rec1.remove_channels(bad_channel_ids)
print('bad_channel_ids', bad_channel_ids)

# Phase shift the data to account for neuropixel sampling offset
rec3 = si.phase_shift(rec2)

# Common median reference the data
rec4 = si.common_reference(rec3, operator="median", reference="global")
rec = rec4
print('rec',rec)

# Look at the data across multiple steps of pre-processing (this doesn't seem to work)
# %matplotlib widget
# si.plot_timeseries({'filter':rec1, 'cmr': rec4}, backend='ipywidgets')

# Look at the rasters at various stages of preprocessing
fig, axs = plt.subplots(ncols=3, figsize=(20, 10))
si.plot_timeseries(rec1, backend='matplotlib',  clim=(-50, 50), ax=axs[0])
si.plot_timeseries(rec4, backend='matplotlib',  clim=(-50, 50), ax=axs[1])
si.plot_timeseries(rec, backend='matplotlib',  clim=(-50, 50), ax=axs[2])
for i, label in enumerate(('filter', 'cmr', 'final')):
    axs[i].set_title(label)
# plt.show() # Uncomment to show plot

# Look at some example traces
fig, ax = plt.subplots(figsize=(20, 10))
some_chans = rec.channel_ids[[100, 150, 200, ]]
si.plot_timeseries({'filter':rec1, 'cmr': rec4}, backend='matplotlib', mode='line', ax=ax, channel_ids=some_chans)
# plt.show() # Uncomment to show plot

# Save the preprocessed file (we need clean up directory structure)
# job_kwargs = dict(n_jobs=40, chunk_duration='1s', progress_bar=True)
# rec = rec.save(folder=base_folder / 'preprocess', format='binary', **job_kwargs)

# Estimate the noise on the scaled traces (microV) or on the raw one (which is in our case int16).
noise_levels_microV = si.get_noise_levels(rec, return_scaled=True)
noise_levels_int16 = si.get_noise_levels(rec, return_scaled=False)
fig, ax = plt.subplots()
_ = ax.hist(noise_levels_microV, bins=np.arange(5, 30, 2.5))
ax.set_xlabel('noise  [microV]')
# Text(0.5, 0, 'noise  [microV]')
# plt.show() # Uncomment to show plot

# # Detect and localize peaks
# from spikeinterface.sortingcomponents.peak_detection import detect_peaks
# job_kwargs = dict(n_jobs=40, chunk_duration='1s', progress_bar=True)
# peaks = detect_peaks(rec,  method='locally_exclusive', noise_levels=noise_levels_int16, detect_threshold=5, local_radius_um=50., **job_kwargs)
# print('peaks',peaks)
# from spikeinterface.sortingcomponents.peak_localization import localize_peaks
# peak_locations = localize_peaks(rec, peaks, method='center_of_mass', local_radius_um=50., **job_kwargs)
# print('peak_locations',peak_locations)

# # Visualize peaks to look for potential drift
# fs = rec.sampling_frequency
# fig, ax = plt.subplots(figsize=(10, 8))
# ax.scatter(peaks['sample_ind'] / fs, peak_locations['y'], color='k', marker='.',  alpha=0.002)
# plt.show()

# # Use peak location estimates to estimate cluster separation prior to sorting
# fig, ax = plt.subplots(figsize=(15, 10))
# si.plot_probe_map(rec, ax=ax, with_channel_ids=True)
# ax.set_ylim(-100, 150)
# ax.scatter(peak_locations['x'], peak_locations['y'], color='purple', alpha=0.002)
# plt.show()

# Do spike sorting

# Check the available spike sorters
availSorters = si.available_sorters()
print('availSorters',availSorters)

# Check the installed spike sorters
installedSorters = si.installed_sorters()
print('installedSorters',installedSorters)

# Check default params for kilosort3
defaultKS3Params = si.get_default_sorter_params('kilosort3')
# print('defaultKS3Params',defaultKS3Params)

# Run kilosort3
sorting = si.run_sorter('kilosort3', rec, output_folder=base_folder / 'kilosort3_output', singularity_image="spikeinterface/kilosort3-compiled-base:latest", verbose=True, **defaultKS3Params)

# # Check default params for kilosort2.5
# defaultKS2_5Params = si.get_default_sorter_params('kilosort2_5')
# # print('defaultKS3Params',defaultKS3Params)

# # Run kilosort3
# sorting = si.run_sorter('kilosort2_5', rec, output_folder=base_folder / 'kilosort2.5_output', singularity_image="spikeinterface/kilosort2_5-compiled-base:latest", verbose=True, **defaultKS2_5Params)







