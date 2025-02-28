from argparse import ArgumentParser
import pandas as pd
from spikeinterface.extractors import read_kilosort, read_binary
from spikeinterface import create_sorting_analyzer
from probeinterface import read_prb

def main():
    print('running sorted.py')
    options = parseInputs()
    spikes2mat(options.sort_folder, options.export_folder)

def spikes2mat(sort_folder, output_path):   
    print('Reading kilosort output from:', sort_folder)
    sorting = read_kilosort(sort_folder+'/sorter_output',keep_good_only=False)

    datPath = sort_folder + '/sorter_output/temp_wh.dat'
    print('Reading binary file:', datPath)
    rec = read_binary(file_paths=datPath, dtype='int16', sampling_frequency=30000.0, num_channels=64) #TODO: get params from params.py

    probe = read_prb(sort_folder+'/sorter_output/probe.prb')
    print('lodading probe:', probe)
    rec = rec.set_probegroup(probe)
    
    # from spikeinterface.curation import remove_excess_spikes
    # sorting = remove_excess_spikes(sorting=sorting, recording=rec)

    print('Creating sorting analyzer')
    sorting_analyzer = create_sorting_analyzer(sorting=sorting, recording=rec, format="memory", n_jobs=8)

    job_kwargs = dict(n_jobs=8, progress_bar=False)
    print('Computing random spikes')
    sorting_analyzer.compute("random_spikes",  **job_kwargs)
    print('Computing waveforms')
    sorting_analyzer.compute("waveforms",  **job_kwargs)
    print('Computing templates')
    sorting_analyzer.compute("templates",  **job_kwargs)
    print('Computing noise levels')
    sorting_analyzer.compute("noise_levels",  **job_kwargs)
    print('Computing principal components')
    sorting_analyzer.compute("principal_components",  **job_kwargs)
    print('Computing spike amplitudes')
    sorting_analyzer.compute("spike_amplitudes", **job_kwargs)
    print('Computing quality metrics')
    sorting_analyzer.compute("quality_metrics", skip_pc_metrics=False,  **job_kwargs)

    templates = sorting_analyzer.get_extension('templates').get_data() # clusters x time x channel
    qualityMetrics = sorting_analyzer.get_extension('quality_metrics').get_data()

    unit_locations = sorting_analyzer.compute(input="unit_locations", method="monopolar_triangulation").get_data()
 


    for id in qualityMetrics.index:
        t = sorting.get_unit_spike_train(unit_id=id, return_times=True)

    group = pd.read_csv(sort_folder+'/sorter_output/cluster_group.tsv', sep='\t', header=0)

    sorting_analyzer.save_as(folder=sort_folder+'/analyzer', format="binary_folder") #Save the analyzer object
    raise Exception('breakpoint')

def parseInputs():
    parser = ArgumentParser(description='Export spikes, quality metrics, and waveforms from sorter output')
    parser.add_argument('--sort_folder', 
        help='Path to data folder',
        required=True
        )
    parser.add_argument('--export_folder', 
        help='Path to data folder',
        required=True
        )
    options = parser.parse_args()
    return options
if __name__ == "__main__":
    main()