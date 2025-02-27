from argparse import ArgumentParser
from os import environ, path
from pathlib import PurePath
from shutil import move
from pandas import read_csv
import yaml
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
    
    if not options['debugWithoutSlurm']: # Move log file to output folder
        logPath = f'{options['jobFolder']}/logs/{options['taskID']}_{options['jobID']}.txt'
        move(logPath, outputPath)

def load_export_settings_from_yaml(yamlFile):
    with open(yamlFile, 'r') as f:
        fullYam = yaml.full_load(f)
    return fullYam.get('export_settings') # returns None if key not found

def get_yaml_settings(jobFolder):
    ## Load default settings from yaml in this git repository
    parentDir = path.dirname(path.realpath(__file__))
    default_yaml = parentDir + '/export_settings.yaml'
    print("Loading default export settings from", default_yaml)
    options = load_export_settings_from_yaml(default_yaml)
            
    ## Load user settings from job folder and overwrite defaults
    user_yaml = jobFolder +'/export_settings.yaml'
    if path.isfile(user_yaml):
        print("Overwriting default export settings with values from", user_yaml)
        user_overrides = load_export_settings_from_yaml(user_yaml)
        if user_overrides:
            options.update(user_overrides)
    return options

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
    
    options.update(get_yaml_settings(options['jobFolder']))

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