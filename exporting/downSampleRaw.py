

from argparse import ArgumentParser
from spikeinterface.extractors import read_openephys
from os import listdir, makedirs, path, environ
from spikeinterface.preprocessing import bandpass_filter
import numpy as np
import pandas as pd
import scipy.io

def main():
    print('running downSampleRaw.py')
    options = parseInputs()
    rec = loadRecording(recPath=options.dataFolder)
    if options.shortenRec:
        rec = shortenRec(rec=rec, timeDur = options.shortenRec)

    unfiltered = downsample(rec, 30000) #temp for testing
    save2mat(unfiltered, options.exportFolder + '/unfiltered.mat')#temp for testing
    rec = bandpass(rec, options.desiredRate)
    filtered = downsample(rec, 30000) #temp for testing
    save2mat(filtered, options.exportFolder + '/filtered.mat')#temp for testing
    downsampled = downsample(rec, options.desiredRate)
    save2mat(downsampled, options.exportFolder + '/downsampled.mat')
    
    

def save2mat(data, fname):
    scipy.io.savemat(fname, data, do_compression=True)
    return
def save2csv(rec, fname):
    # for x in data: #convert numpy arrays to lists before converting to dataframe
    #     data[x] = data[x].tolist()
    # table = pd.DataFrame.from_dict(data)
    # table.to_csv(options.exportFolder + 'traces.csv')
    return
def parseInputs():
    parser = ArgumentParser(description='Spike sort a single recording')
    parser.add_argument('--dataFolder', 
        help='Path to data folder',
        required=True
        )
    parser.add_argument('--exportFolder', 
        help='Path to data folder',
        required=True
        )
    parser.add_argument('--shortenRec',
        help='Shorten the recording to this duration (s)',
        type=int,
        required=False,
        )
    parser.add_argument('--desiredRate',
        help='The final sample rate after downsampling (Hz), Default 1000 Hz',
        type=int,
        required=False,
        default=1000
        )
    options = parser.parse_args()
    return options

def loadRecording(recPath):
    #Load Signal channel data. Have to do this differently depending on which OE version was used to record
    oldOEFiles = [f for f in listdir(recPath) if f.endswith('.continuous')] #Old OE version has .continuous files directly in recording folder
    if oldOEFiles: 
        #Read the ephys data (stream names are 'Signals AUX', 'Signals CH', 'Signals ADC')
        rec = read_openephys(recPath,stream_name='Signals CH')
    else:
        rec = read_openephys(recPath)
        # Pull out signal channels (IDs starting with CH)
        # isSignalChannel = np.char.find(rec.channel_ids, 'CH')==0
        # signalChannels = rec.channel_ids[isSignalChannel]
        # rec = rec.channel_slice(channel_ids=signalChannels)

    # Check if recording has multiple segments
    if rec.get_num_segments() > 1:
        segmentDuration = [rec.get_duration(i) for i in range(rec.get_num_segments())]
        print(f'Raw data contains multiple segments with the following time durations (s): {segmentDuration}. Only the longest segment will be spike sorted')
        rec = rec.select_segments(int(np.argmax(segmentDuration)))
    return rec

def shortenRec(rec, timeDur):
    tstart = rec._get_t_starts()
    start=tstart[0]
    end = tstart[0]+timeDur
    rec = rec.time_slice(start_time=start,end_time=end)
    return rec
def bandpass(rec, desiredRate):
    freq_min=0.0000001 # Using a very low minimum frequency
    freq_max = desiredRate * 0.5 # frequency cuttoff of 80% final sampling frequency. This number used by MATLAB decimate(). Nyquist means 50% sampling frequency is max, but filter isn't perfect.
    return bandpass_filter(recording=rec,freq_min=freq_min,freq_max=freq_max)


def downsample(rec, desiredRate):
    data = dict()
    decimation_factor = round(rec.get_sampling_frequency() / desiredRate)
    t = rec.get_times()
    data['time_stamp'] = t[ : : decimation_factor]

    for id in rec.channel_ids: #break up by channel for less memory usage
        trace = rec.get_traces(channel_ids=[id])
        data[id] = trace[ : : decimation_factor]
        data[id] = np.squeeze(data[id])
    return data

if __name__ == "__main__":
    main()