# This script is designed to load and spike sort open ephys data recorded with neuropixels.
# It is based on this guide: https://spikeinterface.readthedocs.io/en/latest/how_to/analyse_neuropixels.html

import spikeinterface.full as si
import probeinterface as pi
import spikeinterface.widgets as siw
print(si.__version__)

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from probeCreator import probeCreator

# Define the path to the data
base_folder = Path('/N/project/lapishLabWorkspace/Nick2CAPTestData')
openephys_folder = base_folder / '2018-12-11-Session4'

# Read the ephys data (stream names are 'Signals AUX', 'Signals CH', 'Signals ADC')
raw_rec = si.read_openephys(openephys_folder,stream_name='Signals CH')
print('raw_rec',raw_rec)

# Create the probe
probe = probeCreator('NT2CAPCohort2Animal5')
# probe = probeCreator('TestAnimal')
print('Probe:',probe)
# print('Contact Positions:',probe.contact_positions)
stop

# Set the probe into the recording
raw_rec.set_probe(probe, in_place=True, group_mode="by_shank")
# raw_rec.set_probe(probe)
# raw_rec.set_channel_locations(probe.contact_positions)
# print('rec Contact Positions:',raw_rec.get_channel_locations())

# High-pass filter the data
rec1 = si.highpass_filter(raw_rec, freq_min=300.)

noise_levels_microV = si.get_noise_levels(rec1, return_scaled=True)
noise_levels_int16 = si.get_noise_levels(rec1, return_scaled=False)
fig, ax = plt.subplots()
_ = ax.hist(noise_levels_microV, bins=np.arange(5, 30, 2.5))
ax.set_xlabel('noise  [microV]')

# Identify bad channels and remove them
bad_channel_ids, channel_labels = si.detect_bad_channels(rec1,method="std",std_mad_threshold=3)
rec2 = rec1.remove_channels(bad_channel_ids)
print('bad_channel_ids', bad_channel_ids)

noise_levels_microV = si.get_noise_levels(rec2, return_scaled=True)
noise_levels_int16 = si.get_noise_levels(rec2, return_scaled=False)
fig, ax = plt.subplots()
_ = ax.hist(noise_levels_microV, bins=np.arange(5, 30, 2.5))
ax.set_xlabel('noise  [microV]')
plt.show() # Uncomment to show plot

# Common median reference the data
rec3 = si.common_reference(rec2, operator="median", reference="global")
rec = rec3
print('rec',rec)

# Look at the rasters at various stages of preprocessing
fig, axs = plt.subplots(ncols=3, figsize=(20, 10))
si.plot_timeseries(rec1, backend='matplotlib',  clim=(-50, 50), ax=axs[0])
si.plot_timeseries(rec3, backend='matplotlib',  clim=(-50, 50), ax=axs[1])
si.plot_timeseries(rec, backend='matplotlib',  clim=(-50, 50), ax=axs[2])
for i, label in enumerate(('filter', 'cmr', 'final')):
    axs[i].set_title(label)
# plt.show() # Uncomment to show plot

# Look at some example traces
fig, ax = plt.subplots(figsize=(20, 10))
some_chans = rec.channel_ids[[5, 10, 20, ]]
si.plot_timeseries({'filter':rec1, 'cmr': rec3}, backend='matplotlib', mode='line', ax=ax, channel_ids=some_chans)
# plt.show() # Uncomment to show plot

# Estimate the noise on the scaled traces (microV) or on the raw one (which is in our case int16).
noise_levels_microV = si.get_noise_levels(rec, return_scaled=True)
noise_levels_int16 = si.get_noise_levels(rec, return_scaled=False)
fig, ax = plt.subplots()
_ = ax.hist(noise_levels_microV, bins=np.arange(5, 30, 2.5))
ax.set_xlabel('noise  [microV]')
# Text(0.5, 0, 'noise  [microV]')
# plt.show() # Uncomment to show plot

# Get the kilosort3 parameters
KS3Params = si.get_default_sorter_params('kilosort3')
print('KS3Params:',KS3Params)

# Turn off drift correction
KS3Params = {'do_correction': False}

# Increase the NT parameter to avoid EIG did not converge errors
KS3Params = {'NT': 64000}

print('Recording properties:',rec.get_property_keys())

# Run the spike sorting
# sorting = si.run_sorter_by_property('kilosort3', rec, grouping_property='group', working_folder=base_folder / 'kilosort3_output', singularity_image="spikeinterface/kilosort3-compiled-base:latest", verbose=True, **KS3Params)
sorting = si.run_sorter('kilosort3', rec, output_folder=base_folder / 'kilosort3_output', singularity_image="spikeinterface/kilosort3-compiled-base:latest", verbose=True, **KS3Params)
