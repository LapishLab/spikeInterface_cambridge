from argparse import ArgumentParser
from os import environ, path
from pathlib import PurePath
from pandas import read_csv
from rawData import events2mat, stream2mat

def main():
    options = parseInputs()
    rec_settings = getRecordingSettings(options)
    dataSetName = PurePath( rec_settings['dataPath']).name
    outputFolder= f'{dataSetName}__{options['jobID']}_{options['taskID']}'
    outputPath = path.join(options['jobFolder'], 'export', outputFolder)

    events2mat(dataPath=rec_settings['dataPath'], outputPath=outputPath)
    stream2mat(dataPath=rec_settings['dataPath'], outputPath=outputPath)
    # TODO: spikes2Mat(rec_settings['sortPath'],outputPath)

def parseInputs():
    print('parsing inputs')
    parser = ArgumentParser(description='Spike sort a single recording')
    parser.add_argument('--jobFolder', 
                        help='Path to job folder which contains recordingSettings.csv and batchSettings.yaml',
                        required=True
                        )
    parser.add_argument('--debugWithoutSlurm',
                        help='Enable for debugging without submitting to Slurm',
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
    return options

def getRecordingSettings(options):
    print('loading recording settings')
    csvPath = path.join(options['jobFolder'], 'recordingSettings.csv') 
    recCsv = read_csv(csvPath) # load whole rec settings file
    ind = int(options['taskID']) - 1 #subtract 1 for Python indexing by 0
    return recCsv.iloc[ind]

if __name__ == "__main__":
    main()