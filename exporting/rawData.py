

from argparse import ArgumentParser
from spikeinterface.extractors import read_openephys, read_openephys_event
from os import listdir, makedirs
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
        desiredRate=options.desiredRate
    )

def stream2mat(dataPath, outputPath, desiredRate=1000):
    stream = loadRecording(recPath=dataPath)
    stream = resample(stream,desiredRate)

    data = dict() # scipy.io.savemat converts dict to MATLAB struct
    data['time'] = stream.get_times()
    data['traces'] = stream.get_traces()
    data['channels'] = getChannelProperties(stream)
    makedirs(outputPath, exist_ok=True)
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
    eventExtractor = read_openephys_event(dataPath) #TODO: add support for old OE version.
    events = dict()
    for id in eventExtractor.channel_ids:
        newID = id.replace(" ", "_") #MATLAB doesn't like spaces in struct field names
        events[newID] = eventExtractor.get_events(id)
    makedirs(outputPath, exist_ok=True)
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
        rec = read_openephys(recPath,stream_name='Signals CH') # TODO: Load all streams for export, not just 'Signals CH'
    else:
        rec = read_openephys(recPath)

    # Check if recording has multiple segments
    if rec.get_num_segments() > 1: # TODO: handle multiple segments more flexibly
        segmentDuration = [rec.get_duration(i) for i in range(rec.get_num_segments())]
        print(f'Raw data contains multiple segments with the following time durations (s): {segmentDuration}. Only the longest segment will be exported') 
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