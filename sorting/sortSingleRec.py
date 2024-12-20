from datetime import datetime
from spikeinterface.extractors import read_openephys
from spikeinterface.preprocessing import bandpass_filter, common_reference, detect_bad_channels
from spikeinterface.sorters import run_sorter, get_default_sorter_params
from probeinterface import get_probe
import numpy as np
from pathlib import PurePath
from shutil import rmtree, move
from os import listdir
from warnings import warn
from pandas import read_csv
from collections import namedtuple
from argparse import ArgumentParser

def main():
    args = parseInputs()
    paths = getPaths(args)
    probeList,probeNames = createProbes(channelMapPath=paths.channelMap)
    rec = loadRecording(recPath=paths.recording)
    recList = splitRecByProbe(rec=rec,probeList=probeList)
    for i, rec in enumerate(recList):
        rec = preprocess(rec)
        probeFolder = paths.temporaryOutput + '/' + probeNames[i]
        runSorter(rec,savePath=probeFolder)
    saveResults(paths)

def parseInputs():
    parser = ArgumentParser(description='Spike sort a single recording')
    parser.add_argument('--jobFolder', 
                    help='Path to job folder which contains recordingSettings.csv and batchSettings.yaml',
                    required=True
                    )
    parser.add_argument('--taskID', 
                help='Slurm task ID number which will dictate which row is read from recordingSettings.csv',
                type=int,
                default='1'
                )
    return parser.parse_args()
def getPaths(args):
    ## Load recording settings file
    recCsvFile = args.jobFolder +'/recordingSettings.csv' 
    recCsv = read_csv(recCsvFile) # load whole rec settings file
    row = args.taskID - 1 #subtract 1 for Python indexing by 0
    recSettingsRow = recCsv.iloc[row] # pull row for dataset specified by SLURM task ID

    #Get dataset name from path
    dataSetName = PurePath(recSettingsRow['dataPath']).name

    #Save paths to named tuple
    Paths = namedtuple('Paths',['recording', 'channelMap','temporaryOutput', 'finalOutput'])
    paths = Paths(
        recording=recSettingsRow['dataPath'],
        channelMap= recSettingsRow['channelMap'],
        temporaryOutput=args.jobFolder + '/sorted/unfinished_' + dataSetName,
        finalOutput=args.jobFolder + '/sorted/' + dataSetName + 'sorted_' + datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
    )
    return paths
def createProbes(channelMapPath):
    channelMap = read_csv(channelMapPath)
    probeList = []
    probeNames = []
    for probeName, channelInds in channelMap.items():
        probe = get_probe(manufacturer='cambridgeneurotech',probe_name=probeName)
        channelInds -= channelInds.min() #Hack to make sure we are 0 indexing
        probe.set_device_channel_indices(channelInds)
        probeList.append(probe)
        probeNames.append(probeName)

        #pi.plotting.plot_probe(probe)
    return (probeList, probeNames)
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
    print('Signal Recording: ',rec)

    # Check if recording has multiple segments
    if rec.get_num_segments() > 1:
        segmentDuration = [rec.get_duration(i) for i in range(rec.get_num_segments())]
        warn('Raw data contains multiple segments with the following time durations (s):'
            + '\n' + str(segmentDuration)
            + '\n I will just spike sort the longest segment')
        rec = rec.select_segments(int(np.argmax(segmentDuration)))
    return rec
def splitRecByProbe(rec,probeList):
    recChannels = rec.get_channel_ids()
    recList = []
    firstIndex=0
    for probe in probeList:
        lastIndex=firstIndex + len(probe.contact_ids)
        subRec = rec.channel_slice(recChannels[firstIndex:lastIndex])
        subRec = subRec.set_probe(probe, group_mode="by_shank")
        recList.append(subRec)
        firstIndex = lastIndex
    return recList
def preprocess(rec):
    rec = bandpass_filter(recording=rec,freq_min=300.,freq_max=3000.)
    bad_channel_ids, _ = detect_bad_channels(rec,method="std",std_mad_threshold=3)
    rec = rec.remove_channels(bad_channel_ids)
    rec = common_reference(rec, operator="median", reference="global")
    return rec
def runSorter(rec,savePath):
    KS3Params = get_default_sorter_params('kilosort3')
    run_sorter('kilosort3',
        rec,
        output_folder= savePath,
        singularity_image="spikeinterface/kilosort3-compiled-base:latest",
        verbose=True,
        delete_container_files=False,
        **KS3Params)
def saveResults(paths):
    rmtree(paths.finalOutput, ignore_errors=True) # delete old version of this folder if present
    move(paths.temporaryOutput, paths.finalOutput) # move folder to final destination
    print('Spike Sorted Data:',paths.finalOutput)

if __name__ == "__main__":
    main()