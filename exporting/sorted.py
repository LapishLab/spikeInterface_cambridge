from argparse import ArgumentParser
from os import listdir, makedirs, path
from pandas import concat, DataFrame, read_csv
from spikeinterface.extractors import read_kilosort, read_binary
from spikeinterface import create_sorting_analyzer
from probeinterface import read_prb
from scipy.io import savemat
from spikeinterface.curation import remove_excess_spikes

def main():
    print('running sorted.py')
    options = parseInputs()
    spikes2mat(options.sort_folder, options.export_folder)

def spikes2mat(sort_folder, export_folder, time_offset=0): 
    probe_folders = [path.join(sort_folder, f) for f in listdir(sort_folder) if path.isdir(path.join(sort_folder, f)) and f.startswith("probe")]
    if len(probe_folders) == 0:
        raise(f'No probe folders found in {sort_folder}')
    output_tables = []
    for probe_folder in probe_folders:
        print(f'Loading spike info from {probe_folder}')
        probe_dataframe = package_sorter_output(probe_folder)
        probe_dataframe['probe'] = path.basename(probe_folder).strip('probe')
        probe_dataframe['spike_times'] = probe_dataframe['spike_times'] + time_offset
        output_tables.append(probe_dataframe)
    
    clusters = concat(output_tables)
    clusters.replace({None: float('nan')}, inplace=True)
    clusters.columns = [c.replace(' ', '_') for c in clusters.columns] # Replace any spaces with underscores for MATLAB compatibility
    output = dict()
    output['clusters'] = clusters.to_records(index=False)
    makedirs(export_folder, exist_ok=True)
    savemat(export_folder+'/spikes.mat', output, do_compression=True)
    #raise Exception('hacky debug')

def read_sorter_params(params_path): # I could
    params = dict()
    f = open(params_path, "r")
    for line in f:
        if '=' in line:
            (key, val) = line.split('=',maxsplit=1)
            params[key.strip()] = val.strip()
        else:
            print(f'Skipping: {line} in {params_path}. Cannot split by "=" deliminator')
    f.close()

    params['n_channels_dat'] = int(params['n_channels_dat'])
    params['sample_rate'] = float(params['sample_rate'])
    params['dtype'] = params['dtype'].strip("'")
    return params

def load_recording(sorter_output_folder):
    params_path = sorter_output_folder + '/params.py'
    params = read_sorter_params(params_path)
    datPath = sorter_output_folder + '/temp_wh.dat'
    print('Reading binary file:', datPath)
    rec = read_binary(
        file_paths=datPath,
        dtype=params['dtype'], 
        sampling_frequency=params['sample_rate'], 
        num_channels=params['n_channels_dat'])
    probe = read_prb(sorter_output_folder+'/probe.prb')
    print('loading probe:', probe)
    rec = rec.set_probegroup(probe)
    return rec

def load_sorting(sorter_output_folder):
    sorting = read_kilosort(sorter_output_folder,keep_good_only=False)
    # TODO: check that cluster_group.tsv length matches the sorting clusters. This might not be the case if a cluster was missed during curation.
    phy_labels = read_csv(sorter_output_folder+'/cluster_group.tsv', sep='\t', header=0)
    if 'KSLabel' in phy_labels.columns:
        print(f"Warning: this dataset hasn't been manually curated. Using Kilosort labels")
        phy_labels.rename(columns={'KSLabel': 'group'}, inplace=True)  
    noise_ids = phy_labels[phy_labels['group'] == 'noise']['cluster_id'].to_list()
    sorting = sorting.remove_units(noise_ids)
    return (sorting, phy_labels)

def package_sorter_output(probe_folder):
    sorter_output_folder = probe_folder + '/sorter_output'
    print('Reading kilosort output from:', sorter_output_folder)
    rec = load_recording(sorter_output_folder)
    (sorting, phy_labels) = load_sorting(sorter_output_folder)
    sorting = remove_excess_spikes(sorting=sorting, recording=rec)

    sorting_analyzer = create_sorting_analyzer(sorting=sorting, recording=rec, format="memory", n_jobs=8) # For some reason this errors only when using python debugger with at least 1 breakpoint enabled.
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
    print('Computing unit locations')
    sorting_analyzer.compute("unit_locations", method="monopolar_triangulation",  **job_kwargs)
  
    print('Pulling import data and combining in single dictionary')
    templates = sorting_analyzer.get_extension('templates').get_data() # clusters x time x channel
    qualityMetrics = sorting_analyzer.get_extension('quality_metrics').get_data()
    unit_locations = sorting_analyzer.get_extension("unit_locations").get_data()

    # ## TODO: maybe export params used for each computation and also template STD + other potentially interesting values not exported by .get_data()
    # t = templates = sorting_analyzer.get_extension('templates')
    # avg = t.data['average']
    # std = t.data['STD']
    # t.params #{'operators': ['average', 'std'], 'ms_before': 1.0, 'ms_after': 2.0}
    # defaults = sorting_analyzer.get_default_extension_params("templates") 
    # raise Exception("hacky debug")

    unit_list = []
    for ind, id in enumerate(sorting_analyzer.unit_ids):
        unit = dict() # Combine all data types into a single dictionary
        unit['cluster_id'] = id
        unit['phy_label'] = phy_labels.loc[phy_labels['cluster_id']==id, 'group'].iloc[0]
        unit['spike_times'] = sorting.get_unit_spike_train(unit_id=id, return_times=True)
        unit['waveform'] = templates[ind,:,:]
        unit['location'] = unit_locations[ind,:]
        unit.update(qualityMetrics.iloc[ind].to_dict()) 
        unit_list.append(unit)
    return DataFrame(unit_list)

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