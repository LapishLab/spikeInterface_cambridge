# cambridgeTrim
# This script trims the first 40 records and the last record off a Cambridge data set. It is meant to work with cambridgeTrimJob
# which is a job that is submitted to the cluster.

import os
import numpy as np
import sys
import shutil
import csv as csv
import math
import spikeinterface.full as si

### Settings ###

# Set the directory where you wish to store the trimmed data, each in its own directory. 
# This directory will be created if it doesn't already exist.
trimDataDir = '/N/project/lapishLabWorkspace/acuteAlcohol_Curated_trim'

# Record size in bytes
record_size_in_bytes = 2070

### Necessary Preprocessing ###

# Get the task ID
taskID = int(sys.argv[1])
# taskID = 1
print('Task ID:',taskID)

# Create the trimmed data directory, if necessary. 
try:
    os.makedirs(trimDataDir)
except FileExistsError:
    pass

# Load the data set list
f = open('/N/project/lapishLabWorkspace/SpikeInterfaceSpikeSorting/cambridgeRecordingsTrim.txt', 'r')
csvreader = csv.reader(f, delimiter=',')
dataSetList =[]
for row in csvreader:
    dataSetList.append(row)
f.close()


# Get the full path, the data set name, and any time limiting data
dataSetPath = dataSetList[taskID - 1][0]
dataSetName = os.path.basename(os.path.normpath(dataSetPath))
channelMapFile = dataSetList[taskID - 1][1]

# Update the user on what data set is being processed
print('Working on data set:',dataSetName)

if len(dataSetList[taskID - 1]) > 2:
    
    # Get the time info
    timeInfo = dataSetList[taskID - 1][2]

    try:
        startCut = float(timeInfo[:timeInfo.find(':')])
        if timeInfo.find('end') > -1:
            trimMode = 1
            if len(timeInfo) > (timeInfo.find('end') + 3):
                endCut = float(timeInfo[timeInfo.find('end') + 4:])
            else:
                endCut = 0
        else:
            trimMode = 2
            endCut = float(timeInfo[timeInfo.find(':') + 1:])
    except:
        raise TypeError("We could not parse the trim time info. Make sure you have the right formatting.")


    # Create the data set directory in the trimmed directory, if necessary.
    if not os.path.exists(os.path.join(trimDataDir,dataSetName)):
        os.makedirs(os.path.join(trimDataDir,dataSetName))

    # Copy over support files
    shutil.copy(os.path.join(dataSetPath,'all_channels.events'),os.path.join(trimDataDir,dataSetName,'all_channels.events'))
    shutil.copy(os.path.join(dataSetPath,'Continuous_Data.openephys'),os.path.join(trimDataDir,dataSetName,'Continuous_Data.openephys'))
    shutil.copy(os.path.join(dataSetPath,'messages.events'),os.path.join(trimDataDir,dataSetName,'messages.events'))
    shutil.copy(os.path.join(dataSetPath,'settings.xml'),os.path.join(trimDataDir,dataSetName,'settings.xml'))

    # Loop through all of the .continuous files, trim them, and copy over
    for fileName in os.listdir(os.path.normpath(dataSetPath)):
        if fileName.endswith('.continuous'):
        
            # Update the user on what file is being trimmed
            print('Working on file:',fileName)

            # Get the full file paths
            filePath = os.path.join(dataSetPath,fileName)
            trimFilePath = os.path.join(trimDataDir,dataSetName,fileName)
        
            # Open and read the file using memmap
            data = np.memmap(filePath, mode='r', dtype='uint8')
            total_bytes = len(data)

            if trimMode == 1:
                
                # We are trimming from the start and/or end
                
                # Figure out how many bytes to cut
                startCut_bytes = math.ceil(startCut/(1024/30000))*record_size_in_bytes
                endCut_bytes = math.ceil(endCut/(1024/30000))*record_size_in_bytes

                # Truncate the data and save it to a new file
                if startCut > 0:
                    header_bytes = data[:1024]
                    trimmed_data = np.concatenate((header_bytes, data[1024+startCut_bytes:total_bytes-endCut_bytes]))
                    trimmed_data.tofile(trimFilePath)
                else:
                    data[:total_bytes - endCut_bytes].tofile(trimFilePath)
            
            else:
            
                # We are trimming to a set window

                # Figure out how many bytes to cut
                startCut_bytes = math.ceil(startCut/(1024/30000))*record_size_in_bytes
                endCut_bytes = math.floor(endCut/(1024/30000))*record_size_in_bytes

                # Truncate the data and save it to a new file
                if startCut > 0:
                    header_bytes = data[:1024]
                    trimmed_data = np.concatenate((header_bytes, data[1024+startCut_bytes:1024+endCut_bytes]))
                    trimmed_data.tofile(trimFilePath)
                else:
                    data[:1024+endCut_bytes].tofile(trimFilePath)

    # Load the original and trimmed data set to test loading functionality and to report changes in length
    try:
        origRec = si.read_openephys(dataSetPath,stream_name='Signals CH')
        print('Original Recording:',OrigRec)
    except:
        print('Original Recording failed to load.')
    
    # No try/except check here to allow the job to error if the trimmed data set won't load
    trimRec = si.read_openephys(os.path.join(trimDataDir,dataSetName),stream_name='Signals CH')
    print('Trimmed Recording:',trimRec)
    



else:
    print("This data set has no time trimming info, so no trimming was performed and the data set was not copied.")