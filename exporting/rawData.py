

from argparse import ArgumentParser
from spikeinterface.extractors import read_openephys
from os import listdir
import numpy as np
from scipy.io import savemat
from spikeinterface.preprocessing import resample

def main():
    print('running downSampleRaw.py')
    options = parseInputs()
    rec = loadRecording(recPath=options.dataFolder)
    if options.shortenRec:
        rec = shortenRec(rec=rec, timeDur = options.shortenRec)

    # rec2mat(rec, options.exportFolder + '/unfiltered.mat')# TODO: remove temp for testing
    rec = resample(rec,options.desiredRate)
    rec2mat(rec, options.exportFolder + '/downsampled.mat')
     

def rec2mat(rec, fname):
    data = dict() # scipy.io.savemat converts dict to MATLAB struct
    data['time'] = rec.get_times()
    data['traces'] = rec.get_traces()

    # Create structured array of all Channel properties
    channel_properties = rec.get_property_keys() # get field names (e.g. channel_name)
    data_format = [rec.get_property(f).dtype for f in channel_properties] # get data type of each field
    dtype = np.dtype({'names':channel_properties ,'formats': data_format}) # create a numpy dtype object with field names and data type
    numChannels = rec.get_num_channels()
    channels = np.empty(numChannels, dtype=dtype) # create empty structured array
    for prop in channel_properties:
        channels[prop] = rec.get_property(prop)  # assign values to structured array
    data['channels'] = channels

    savemat(fname, data, do_compression=True)
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

if __name__ == "__main__":
    main()