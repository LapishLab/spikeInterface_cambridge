# This script is designed to create a small fake recording to run through spike sorting to 
# test that it works

import spikeinterface.full as si
from spikeinterface.extractors import toy_example

test_recording, _ = toy_example(duration=120, seed=0, num_channels=64,num_segments=1)
test_recording = test_recording.save(folder="/N/project/lapishLabWorkspace/NickSpikeInterfaceTest")

defaultKS3Params = si.get_default_sorter_params('kilosort3')

# sorting = si.run_sorter('kilosort3', recording=test_recording, output_folder="kilosort3", singularity_image=True)
sorting = si.run_sorter('kilosort3', recording=test_recording, output_folder='/N/project/lapishLabWorkspace/NickSpikeInterfaceTest/kilosort3_output', singularity_image="spikeinterface/kilosort3-compiled-base:latest", verbose=True, **defaultKS3Params)
print(sorting)


