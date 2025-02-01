from datetime import datetime
from spikeinterface.extractors import read_openephys
from spikeinterface.preprocessing import bandpass_filter, common_reference, detect_bad_channels
from spikeinterface.sorters import run_sorter, get_default_sorter_params
from probeinterface import get_probe
import numpy as np
from pathlib import PurePath
from shutil import rmtree, move, copy2
from os import listdir, makedirs, path, chdir, environ
from warnings import warn
from pandas import read_csv
from collections import namedtuple
from argparse import ArgumentParser
from subprocess import check_output
from pprint import pp, pformat
from git import Repo
import pickle
import logging
log = logging.getLogger(__name__)

def main():
    print('running sortSingleRec.py')
    options = parseInputs()
    log = logInfo(options)
    fullRec = loadRecording(recPath=options['paths']['rawData'])
    if options['shortenRec']:
        fullRec = shortenRec(rec=fullRec, timeDur = options['shortenRec'])
    probes = createProbes(channelMapPath=options['paths']['channelMap'])
    recList = splitRecByProbe(rec=fullRec,probes=probes)
    for i, d in enumerate(recList):
        d['rec'] = preprocess(rec=d['rec'])
        savePath = options['paths']['probeOutput'][i]
        runSorter(rec=d['rec'], savePath=savePath)
    saveResults(options)

def logInfo(options):
    # Save our logger to a custom file
    log.setLevel(logging.INFO)
    log.addHandler(logging.FileHandler(options['paths']['myLog']))
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log.handlers[0].setFormatter(formatter)

    from spikeinterface import __version__ as si_version
    log.info(f'SpikeInterface version = {si_version}')
    log.info(pformat(options))
    
    scriptPath = path.dirname(path.abspath(__file__))
    repo = Repo(scriptPath, search_parent_directories=True)
    sha = repo.head.object.hexsha
    log.info(f'Git Commit = {sha}')
def shortenRec(rec, timeDur):
    tstart = rec._get_t_starts()
    start=tstart[0]
    end = tstart[0]+timeDur
    rec = rec.time_slice(start_time=start,end_time=end)
    return rec
def parseInputs():
    parser = ArgumentParser(description='Spike sort a single recording')
    parser.add_argument('--jobFolder', 
                        help='Path to job folder which contains recordingSettings.csv and batchSettings.yaml',
                        required=True
                        )
    parser.add_argument('--debugWithoutSlurm',
                        help='Enable for debugging without submitting to Slurm',
                        required=False,
                        )
    parser.add_argument('--shortenRec',
                    help='Shorten the recording to this duration (s)',
                    type=int,
                    required=False,
                    )
    args = parser.parse_args()
    options = vars(args) # Convert to dictionary so additional settings can be added

    if options['debugWithoutSlurm']:
        options['taskID'] = '1'
        options['jobID'] = None
    else:
        options['taskID'] = environ['SLURM_ARRAY_TASK_ID']
        options['jobID'] = environ['SLURM_ARRAY_JOB_ID']

    
    options['paths'] = getPaths(options)
    return options
def getPaths(options):
    paths = dict() # Save paths in dictionary

    paths['batch']  = path.join(options['jobFolder'], 'batchSettings.yaml')
    ## Load recording settings file
    paths['recCsv'] = path.join(options['jobFolder'], 'recordingSettings.csv') 
    
    recCsv = read_csv(paths['recCsv']) # load whole rec settings file
    ind = int(options['taskID']) - 1 #subtract 1 for Python indexing by 0
 
    paths['rawData'] = recCsv.iloc[ind]['dataPath']
    paths['channelMap'] = recCsv.iloc[ind]['channelMap']
    
    ## Setup output folders
    dataSetName = PurePath( paths['rawData']).name
    now = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
    baseName = f'{options['taskID']}_rec-{dataSetName}_sort-{now}'
    paths['results'] = path.join(options['jobFolder'], 'results', baseName)
    channelMap = read_csv(paths['channelMap'])
    paths['probeOutput'] = []
    for i in range(len(channelMap.columns)):
        paths['probeOutput'].append(path.join(paths['results'], f'probe{i}'))

    paths['metaData'] =  path.join(paths['results'], 'jobMetaData')
    makedirs(paths['metaData'], exist_ok=True)
    paths['myLog'] = path.join(paths['metaData'], 'sortSingleRec.log')
    ## Specify the expected location of the Slurm log file
    if options['debugWithoutSlurm']:
        paths['slurmLog'] = None
    else:
        logBasename = f'{options['taskID']}_{options['jobID']}.txt' 
        paths['slurmLog'] = path.join(options['jobFolder'], 'logs', logBasename)
    return paths
def createProbes(channelMapPath):
    channelMap = read_csv(channelMapPath)
    probes = [] #list of dictionaries
    for probeName, channelInds in channelMap.items():
        log.info(f'Creating probe {probeName}')
        d = dict()
        d['probeName'] = probeName
        d['probe'] = get_probe(manufacturer='cambridgeneurotech',probe_name=probeName)
        channelInds -= channelInds.min() #Hack to make sure we are 0 indexing
        d['probe'].set_device_channel_indices(channelInds)
        probes.append(d)
        #pi.plotting.plot_probe(d['probe'])
    return probes
def loadRecording(recPath):
    #Load Signal channel data. Have to do this differently depending on which OE version was used to record
    oldOEFiles = [f for f in listdir(recPath) if f.endswith('.continuous')] #Old OE version has .continuous files directly in recording folder
    if oldOEFiles: 
        #Read the ephys data (stream names are 'Signals AUX', 'Signals CH', 'Signals ADC')
        rec = read_openephys(recPath,stream_name='Signals CH')
    else:
        rec = read_openephys(recPath)
        # Pull out signal channels (IDs starting with CH)
        isSignalChannel = np.char.find(rec.channel_ids, 'CH')==0
        signalChannels = rec.channel_ids[isSignalChannel]
        rec = rec.channel_slice(channel_ids=signalChannels)
    logging.info('Signal Recording: %s', rec)

    # Check if recording has multiple segments
    if rec.get_num_segments() > 1:
        segmentDuration = [rec.get_duration(i) for i in range(rec.get_num_segments())]
        log.warning(f'Raw data contains multiple segments with the following time durations (s): {segmentDuration}. Only the longest segment will be spike sorted')
        rec = rec.select_segments(int(np.argmax(segmentDuration)))
    return rec
def splitRecByProbe(rec,probes):
    recChannels = rec.get_channel_ids()
    firstIndex=0
    for d in probes:
        lastIndex=firstIndex + len(d['probe'].contact_ids)
        d['rec'] = rec.channel_slice(recChannels[firstIndex:lastIndex])
        d['rec'] = d['rec'].set_probe(d['probe'], group_mode="by_shank")
        firstIndex = lastIndex
    return probes
def preprocess(rec):
    log.info(f'preprocessing: {rec}')
    rec = bandpass_filter(recording=rec,freq_min=300.,freq_max=3000.)
    bad_channel_ids, _ = detect_bad_channels(rec,method="std",std_mad_threshold=3)
    rec = rec.remove_channels(bad_channel_ids)
    rec = common_reference(rec, operator="median", reference="global")
    return rec
def runSorter(rec,savePath):
    sorterParameters = dict()
    sorterParameters['do_correction'] = False
    sorterParameters['save_preprocessed_copy'] = True
    # sorterParameters['skip_kilosort_preprocessing'] = True
    # sorterParameters['nearest_templates'] = rec.get_num_channels()
    #sorterParameters['min_template_size'] = 10 #may need to be decreased for smaller spacing

    log.info(f'sorting: {rec}')
    run_sorter(
        sorter_name='kilosort4',
        recording=rec,
        folder=savePath,
        verbose=True,
        remove_existing_folder=True,
        raise_error=True,
        **sorterParameters)
def saveResults(options):
    metaDataFolder = options['paths']['metaData']

    # copy settings and log files
    copy2(options['paths']['channelMap'], metaDataFolder)
    copy2(options['paths']['recCsv'], metaDataFolder)
    copy2(options['paths']['batch'] , metaDataFolder)
    log.info('Job completed successfully')
    
    # Copy log file to final destination if it exists (no log file if running in debug mode)
    if options['paths']['slurmLog']: 
        copy2(options['paths']['slurmLog'], metaDataFolder)

if __name__ == "__main__":
    main()