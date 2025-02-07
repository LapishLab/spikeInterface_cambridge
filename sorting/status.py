
import sys
import subprocess
import time
import pandas as pd

jobFolder = sys.argv[1]
jobID = sys.argv[2]

def main():
    statusFile = f'{jobFolder}/{jobID}_status.csv'
    waitTime = 5*60 # 5 minutes
    time.sleep(10) # wait a little bit to give time for Slurm to register the job 
    status = pollStatus(statusFile, waitTime)
    reportFile = f'{jobFolder}/{jobID}_report.csv'
    saveReport(reportFile, status)
    import cleanup
    cleanup.cleanup(statusFile)

def pollStatus(statusFile, waitTime):
    cmd=f'sacct --jobs={jobID} -X --format=JobID,State,CPUTime,TimeLimit,ExitCode'
    keepPolling = True
    while keepPolling:
        resp = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        table = parseResponse(resp.stdout)
        table.to_csv(statusFile, index=False)

        nonePending = not table['State'].str.contains("PENDING").any()
        noneRunning = not table['State'].str.contains("RUNNING").any()
        if nonePending and noneRunning:
            return table
        time.sleep(waitTime)

def saveReport(reportFile, status):  
    reportDict = dict()
    for id in status['JobID']:
        cmd=f'seff {id}'
        resp = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        rows = resp.stdout.strip().split('\n')
        for row in rows:
            header, data= row.split(':', 1)
            if header in reportDict:
                reportDict[header].append(data)
            else:
                reportDict[header] = [data]
    pd.DataFrame.from_dict(reportDict).to_csv(reportFile, index=False) 

def parseResponse(respString):
    rows = respString.strip().split('\n')
    listOfLists = [row.split() for row in rows]
    data = listOfLists[2:] # first row is header, 2nd row is dashes
    headers = listOfLists[0]
    return pd.DataFrame(data, columns=headers)

if __name__ == "__main__":
    main()
