

from argparse import ArgumentParser
from time import time
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
    streams = load_streams(recPath=dataPath)
    streams = [resample(s, desiredRate) for s in streams]

    data = dict() # scipy.io.savemat converts dict to MATLAB struct
    data['time'] = streams[0].get_times()
    data['traces'] = getTraces(streams[0])
    data['channels'] = getChannelProperties(streams[0])
    
    if len(streams)>1:
        for s in streams[1:]:
            data['traces'] = np.concatenate((data['traces'],getTraces(s)), axis=1)
            data['channels'] = np.concatenate((data['channels'],getChannelProperties(s)), axis=0)

    makedirs(outputPath, exist_ok=True)
    stream_mat = outputPath+'/stream.mat'
    print(f"Saving stream data to {stream_mat}")
    savemat(stream_mat, data, do_compression=True)

def getTraces(stream):
    # Preallocate an empty ndarray
    num_channels = stream.get_num_channels()
    num_samples = stream.get_num_samples()
    print(f"Preallocating array for traces")
    traces = np.empty((num_samples, num_channels), dtype=stream.dtype)

    # Fill in the columns of the empty ndarray
    for ind, id in enumerate(stream.channel_ids):
        traces[:, ind] = stream.get_traces(channel_ids=[id]).flatten()
        print(f"{id} trace retrieved")
    return traces

def getChannelProperties(stream):
    # Create structured array of all Channel properties
    print("Getting channel properties")
    channel_properties = stream.get_property_keys() # get field names (e.g. channel_name)
    data_format = [stream.get_property(f).dtype for f in channel_properties] # get data type of each field
    dtype = np.dtype({'names':channel_properties ,'formats': data_format}) # create a numpy dtype object with field names and data type
    numChannels = stream.get_num_channels()
    channels = np.empty(numChannels, dtype=dtype) # create empty structured array
    for prop in channel_properties:
        channels[prop] = stream.get_property(prop)  # assign values to structured array
    return channels

def events2mat(dataPath, outputPath):
    print(f'Loading event data from {dataPath}')
    if is_legacy_OE_recording(dataPath):
        events = load_legacy_events(dataPath)
    else: 
        events = load_current_events(dataPath)
    makedirs(outputPath, exist_ok=True)
    event_mat = outputPath+'/events.mat'
    print(f"Saving event data to {event_mat}")
    savemat(event_mat, events, do_compression=True)

def load_current_events(dataPath):
    from open_ephys.analysis import Session
    session = Session(dataPath)
    rec_node = session.recordnodes[0]
    rec = rec_node.recordings[0]
    
    df = rec.events
    events = dict()
    events['data'] = df.to_records()
    events['info'] = rec.info['events']
    events['format'] = rec.format
    return events

def load_legacy_events(dataPath):
    from legacy_open_ephys.analysis import Session
    session = Session(dataPath)
    samplerate = get_samplerate_from_xml(dataPath+'/Continuous_Data.openephys')
    df = session.recordings[0].events
    df['timestamp'] = df['timestamp'] / samplerate
    events = dict()
    events['data'] = df.to_records()
    events['format'] = 'legacy_OE'
    return events

def get_samplerate_from_xml(file_path):
    import xml.etree.ElementTree as ET
    root = ET.parse(file_path).getroot()
    for elem in root.iter():
        if 'samplerate' in elem.attrib:
            return float(elem.attrib['samplerate'])
    raise ValueError("samplerate not found in the XML file")
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

def is_legacy_OE_recording(recPath):
    rec_contents = listdir(recPath)
    return [f for f in rec_contents if f.endswith('.continuous')]

def load_streams(recPath):
    print(f'Loading stream info from {recPath}')
    legacy_files = is_legacy_OE_recording(recPath)
    if legacy_files:
        streams = []
        # This seems super hacky, but SI doesn't seem to give any way to check what streams are present in the recording.
        has_CH = [f for f in legacy_files if '_CH' in f] 
        has_AUX = [f for f in legacy_files if '_AUX' in f]
        has_ADC = [f for f in legacy_files if '_ADC' in f]
        if has_CH:
            streams.append(read_openephys(recPath,stream_name='Signals CH'))
        if has_AUX:
            streams.append(read_openephys(recPath,stream_name='Signals AUX'))
        if has_ADC:
            streams.append(read_openephys(recPath,stream_name='Signals ADC'))
    else:
        rec = read_openephys(recPath)
        # Check if recording has multiple segments
        if rec.get_num_segments() > 1: # TODO: handle multiple segments more flexibly
            segmentDuration = [rec.get_duration(i) for i in range(rec.get_num_segments())]
            print(f'Raw data contains multiple segments with the following time durations (s): {segmentDuration}. Only the longest segment will be exported') 
            rec = rec.select_segments(int(np.argmax(segmentDuration)))
        streams = [rec]
    return streams

def shortenRec(rec, timeDur):
    tstart = rec._get_t_starts()
    start=tstart[0]
    end = tstart[0]+timeDur
    rec = rec.time_slice(start_time=start,end_time=end)
    return rec

if __name__ == "__main__":
    main()