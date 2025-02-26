

from argparse import ArgumentParser
from spikeinterface.extractors import read_openephys, read_openephys_event
from os import listdir
import numpy as np
from scipy.io import savemat
from spikeinterface.preprocessing import resample

def main():
    print('running downSampleRaw.py')
    options = parseInputs()
    events2mat(
        dataPath=options.dataFolder,
        outputPath=options.exportFolder
    )
    stream2mat(
        dataPath=options.dataFolder,
        outputPath=options.exportFolder,
        shortenRec=options.shortenRec,
        desiredRate=options.desiredRate
    )

def stream2mat(dataPath, outputPath, shortenRec=None, desiredRate=1000):
    stream = loadRecording(recPath=dataPath, shortenRec=shortenRec)
    stream = resample(stream,desiredRate)

    data = dict() # scipy.io.savemat converts dict to MATLAB struct
    data['time'] = stream.get_times()
    data['traces'] = stream.get_traces()
    data['channels'] = getChannelProperties(stream)
    savemat(outputPath+'/stream.mat', data, do_compression=True)

def getChannelProperties(stream):
    # Create structured array of all Channel properties
    channel_properties = stream.get_property_keys() # get field names (e.g. channel_name)
    data_format = [stream.get_property(f).dtype for f in channel_properties] # get data type of each field
    dtype = np.dtype({'names':channel_properties ,'formats': data_format}) # create a numpy dtype object with field names and data type
    numChannels = stream.get_num_channels()
    channels = np.empty(numChannels, dtype=dtype) # create empty structured array
    for prop in channel_properties:
        channels[prop] = stream.get_property(prop)  # assign values to structured array
    return channels

def events2mat(dataPath, outputPath):
    events = read_openephys_event(dataPath)
    savemat(outputPath+'/events.mat', events, do_compression=True)

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

def loadRecording(recPath, shortenRec=None):
    #Load Signal channel data. Have to do this differently depending on which OE version was used to record
    oldOEFiles = [f for f in listdir(recPath) if f.endswith('.continuous')] #Old OE version has .continuous files directly in recording folder
    if oldOEFiles: 
        #Read the ephys data (stream names are 'Signals AUX', 'Signals CH', 'Signals ADC')
        rec = read_openephys(recPath,stream_name='Signals CH') # TODO: Load all streams for export, not just 'Signals CH'
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

    if shortenRec:
        rec = shortenRec(rec=rec, timeDur=shortenRec)
    return rec

def shortenRec(rec, timeDur):
    tstart = rec._get_t_starts()
    start=tstart[0]
    end = tstart[0]+timeDur
    rec = rec.time_slice(start_time=start,end_time=end)
    return rec

if __name__ == "__main__":
    main()