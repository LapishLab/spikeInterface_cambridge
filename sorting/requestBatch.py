
import os.path as path
import sys
import yaml
import pandas #had to add python module to default modules to enable this import
import subprocess

def main():
    jobFolder = getJobFolder()
    recSettings = getRecordingSettings(jobFolder=jobFolder)
    batchSettings = getBatchSettings(jobFolder=jobFolder, recSettings=recSettings)
    sendBatchRequest(batchSettings=batchSettings, jobFolder=jobFolder)

def getJobFolder():
    ## Check that valid job folder was provided as argument
    if len(sys.argv)>1:
        jobFolder = sys.argv[1]
        jobFolder = path.normpath(jobFolder)
    else:
        raise Exception("No job folder provided (1st positional argument)")

    if not path.isdir(jobFolder):
        raise Exception("Job folder is not a valid directory: " + jobFolder)
    return jobFolder
def getBatchSettings(jobFolder, recSettings):
    ## Load default settings
    parentDir = path.dirname(path.realpath(__file__))
    defaultFile = parentDir + '/examples/batchSettings.yaml'
    with open(defaultFile, 'r') as f:
            batchSettings = yaml.full_load(f)
            
    ## Load batch settings from job folder and overwrite with defined values
    batchSettingFile = jobFolder +'/batchSettings.yaml'
    if path.isfile(batchSettingFile):
        with open(batchSettingFile, 'r') as f:
            userSettings = yaml.full_load(f)
        for key, value in userSettings.items():
            batchSettings[key] = value

    ## Compute missing values if null
    if batchSettings['time'] is None or batchSettings['mem'] is None:
        maxRec = calcMaxRec(recPaths=recSettings['dataPath'])
        if batchSettings['time'] is None:
            batchSettings['time'] = str(round(maxRec*2))
        if batchSettings['mem'] is None:
            batchSettings['mem'] = str(round(maxRec*3)) + 'GB'
    if batchSettings['array'] is None:
        batchSettings['array'] = '1-'+str(len(recSettings))
    if batchSettings['job-name'] is None:
        batchSettings['job-name'] = path.split(jobFolder)[1]
    if batchSettings['output'] is None:
        batchSettings['output'] = jobFolder+'/logs/%a_%j.txt'
    return batchSettings
def calcMaxRec(recPaths):
    maxRec = 0
    for p in recPaths:
        shellResp = subprocess.check_output(['du','-s', p])
        recSize = int(shellResp.split()[0])
        if recSize>maxRec:
            maxRec = recSize
    maxRec = maxRec / 1e6 #convert to GB
    return maxRec
def getRecordingSettings(jobFolder):
    ## Load recording files
    recSettingsFile = jobFolder +'/recordingSettings.csv'
    if not path.isfile(recSettingsFile):
        raise Exception("Recording settings file not found at: " + recSettingsFile)
    recSettings = pandas.read_csv(recSettingsFile)

    ## Check that recording paths are valid directories
    for p in recSettings['dataPath']:
        if not path.isdir(p):
            raise Exception(p + "is not a valid directory path")
        
    ## Check that channel map exists in job folder
    for m in recSettings['channelMap']:
        mapPath = jobFolder+'/'+m
        if not path.isfile(mapPath):
            raise Exception("no channel map found at: \n" + mapPath)
    return recSettings
def sendBatchRequest(batchSettings, jobFolder):
    ## get path to batch job and python sorting script
    parentDir = path.dirname(path.realpath(__file__))
    batchFile = parentDir + "/batch.sh"
    sortingScript = parentDir + "/sortSingleRec.py"

    ## Build Shell command
    cmd = "sbatch" # start of command
    for key, value in batchSettings.items(): 
        cmd += ' --' + key + '=' + value # add option flags and values
    cmd +=" " + batchFile
    cmd +=" " + sortingScript #1st input to batch.sh 
    cmd +=" " + jobFolder #2nd input to batch.sh, and 1st input to sortSingleRec.py

    ## Run Batch shell command
    print(cmd)
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    main()

