#!//N/u/lapishla/BigRed200/.conda/envs/si_ks4/bin/python
import os.path as path
import sys
import yaml
import pandas #had to add python module to default modules to enable this import
import subprocess

def main():
    jobFolder = getJobFolder()
    recSettings = getRecordingSettings(jobFolder=jobFolder)
    batchSettings = get_slurm_settings(jobFolder=jobFolder, recSettings=recSettings)
    resp = sendBatchRequest(batchSettings=batchSettings, jobFolder=jobFolder)
    startStatusUpdater(ShellResp=resp, jobFolder=jobFolder)

def getJobFolder():
    ## Check that valid job folder was provided as argument
    if len(sys.argv)>1:
        jobFolder = sys.argv[1]
        jobFolder = path.normpath(jobFolder)
    else:
        raise Exception("No job folder provided (1st positional argument)")

    if not path.isdir(jobFolder):
        raise Exception("Job folder is not a valid directory: " + jobFolder)
    
    print("Job folder exists")
    return jobFolder

def load_slurm_settings_from_yaml(yamlFile):
    with open(yamlFile, 'r') as f:
        fullYam = yaml.full_load(f)
    return fullYam['slurm_settings']

def get_slurm_settings(jobFolder, recSettings):
    ## Load default settings from yaml in this git repository
    parentDir = path.dirname(path.realpath(__file__))
    default_yaml = parentDir + '/exporting/export_settings.yaml'
    print("Loading default export settings from", default_yaml)
    slurm_settings = load_slurm_settings_from_yaml(default_yaml)
            
    ## Load user settings from job folder and overwrite defaults
    user_yaml = jobFolder +'/export_settings.yaml'
    if path.isfile(user_yaml):
        print("Overwriting default export settings with values from", user_yaml)
        user_overides = load_slurm_settings_from_yaml(user_yaml)
        for key, value in user_overides.items():
            slurm_settings[key] = value

    ## Compute missing values if null
    if slurm_settings['time'] is None or slurm_settings['mem'] is None:
        maxRec = calcMaxRec(recPaths=recSettings['dataPath'])
        if slurm_settings['time'] is None:
            slurm_settings['time'] = str(round(maxRec*2))
            print("time auto-estimated: ", slurm_settings['time'])
        if slurm_settings['mem'] is None:
            slurm_settings['mem'] = str(round(maxRec*3)) + 'GB'
            print("mem auto estimated: ", slurm_settings['mem'])

    ## Set automatic values
    slurm_settings['array'] = '1-'+str(len(recSettings))
    slurm_settings['job-name'] = path.split(jobFolder)[1]
    slurm_settings['output'] = jobFolder+'/logs/%a_%A.txt'
    slurm_settings['nodes'] = '1'
    slurm_settings['ntasks-per-node'] = '1'

    print("log file at: ", slurm_settings['output'])
    print("(%%a = array ID, %%A = master job ID)")
    return slurm_settings
def calcMaxRec(recPaths):
    maxRec = 0
    for p in recPaths:
        shellResp = subprocess.check_output(['du','-s', p])
        recSize = int(shellResp.split()[0])
        if recSize>maxRec:
            maxRec = recSize
    maxRec = maxRec / 1e6 #convert to GB
    print("Max recording size = ", maxRec, "GB")
    return maxRec
def getRecordingSettings(jobFolder):
    ## Load recording files
    recSettingsFile = jobFolder +'/recordingSettings.csv'
    if path.isfile(recSettingsFile):
        print("Recording settings file found at", recSettingsFile)
    else:
        raise Exception("Recording settings file not found at: " + recSettingsFile)
    
    recSettings = pandas.read_csv(recSettingsFile)

    ## Check that recording paths are valid directories
    for p in recSettings['dataPath']:
        if not path.isdir(p):
            raise Exception(p + "is not a valid directory path")
    print("All recording paths are valid directories")
    return recSettings
def sendBatchRequest(batchSettings, jobFolder):
    ## get path to batch job and python sorting script
    parentDir = path.dirname(path.realpath(__file__))
    batchFile = parentDir + "/exporting/batch.sh"
    exportScript = parentDir + "/exporting/export.py"

    ## Build Shell command
    cmd = "sbatch" # start of command
    for key, value in batchSettings.items(): 
        cmd += ' --' + key + '=' + value # add option flags and values
    cmd +=" " + batchFile
    cmd +=" " + exportScript #1st input to batch.sh 
    cmd +=" " + jobFolder #2nd input to batch.sh, and 1st input to sortSingleRec.py

    ## Run Batch shell command
    #print(cmd)
    resp = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    if resp.returncode:
        raise ChildProcessError(resp.stderr)
    else:
        return resp.stdout

def startStatusUpdater(ShellResp, jobFolder):
    # Parse SlurmID from shell response
    import re
    match = re.search('Submitted batch job (.*)\n', ShellResp)
    if match:
        SlurmID = match.group(1)
    else:
        raise Exception("Could not parse job number for status script")
    
    ## get path to status script
    parentDir = path.dirname(path.realpath(__file__))
    statusPy = parentDir + "/sorting/status.py"

    # Run status script in background
    cmd = f'nohup python {statusPy} {jobFolder} {SlurmID} > /dev/null 2>&1 &' #redirect output and error to /dev/null to avoid nohup.out clutter
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    main()

