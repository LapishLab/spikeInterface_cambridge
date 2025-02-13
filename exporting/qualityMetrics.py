
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



def main():

    # sortPath = '/N/u/lapishla/Quartz/Desktop/lapishLabWorkspace/DualProbes/sortAll/sorted/2024-05-10_11-24-32/ASSY-236-E-1/sorter_output'
    # recPath = '/N/u/lapishla/Quartz/Desktop/lapishLabWorkspace/DualProbes/2024-05-10-Session 2/2024-05-10_11-24-32'
    # mapPath = '/N/project/lapishLabWorkspace/ChannelMaps/BaoDualProbe_rat12.csv'
    # #args = parseInputs()
    # #paths = getPaths(args)
    # probeList,probeNames = createProbes(channelMapPath=mapPath)
    # rec = loadRecording(recPath=recPath)
    # recList = splitRecByProbe(rec=rec,probeList=probeList)

    # import pickle
    # pickleName = '/N/project/lapishLabWorkspace/Phillip/results/1_rec-2024-10-17_15-06-39_TN11_sort-2025-01-28_14-24-49/recList.pkl'
    # dbfile = open(pickleName, 'rb')    
    # db = pickle.load(dbfile)
    # dbfile.close()

    # for d in db:
    #     sortPath = path.join(d["finalPath"], 'sorter_output')
    #     sorting= read_kilosort(sortPath,keep_good_only=False)
    #     rec = d['rec'].set_probe(d['probe'], group_mode="by_shank") #Not sure why probe needs to be set again
    #     print(sorting)
    #     print(rec)
    #     sorting_analyzer = create_sorting_analyzer(sorting=sorting, recording=rec, format="memory", n_jobs=8)
    #     print(sorting_analyzer)

    # from spikeinterface import load_extractor
    # rec = load_extractor(sortFolder+'/spikeinterface_recording.json')


    from spikeinterface.extractors import read_kilosort
    # sortFolder = '/N/project/lapishLabWorkspace/DualProbes/sortAll_ks4/KS4_NoDriftCorrection/2024-05-02_10-28-00__4322346_1/probe0'
    sortFolder = '/N/project/lapishLabWorkspace/KS_comparison/KS4_nearestTemplate64/openEphysData12_04_PV4__4320350_3/probe0' #Originally 165, after phy 161 (top cluster #=168)
    print('Reading kilosort output from:', sortFolder)
    sorting = read_kilosort(sortFolder+'/sorter_output',keep_good_only=False)

    from spikeinterface.extractors import read_binary
    datPath = sortFolder + '/sorter_output/temp_wh.dat'
    print('Reading binary file:', datPath)
    rec = read_binary(file_paths=datPath, dtype='int16', sampling_frequency=30000.0, num_channels=64) #TODO: get params from params.py

    from probeinterface import read_prb
    probe = read_prb(sortFolder+'/sorter_output/probe.prb')
    print('lodading probe:', probe)
    rec = rec.set_probegroup(probe)
    
    # from spikeinterface.curation import remove_excess_spikes
    # sorting = remove_excess_spikes(sorting=sorting, recording=rec)

    from spikeinterface import create_sorting_analyzer
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

    group = pd.read_csv(sortFolder+'/sorter_output/cluster_group.tsv', sep='\t', header=0)

    sorting_analyzer.save_as(folder=sortFolder+'/analyzer', format="binary_folder") #Save the analyzer object
    raise Exception('breakpoint')


if __name__ == "__main__":
    main()