import os
import sys
import shutil
import pandas as pd

def cleanup(report_file, dry_run=False):
    df = pd.read_csv(report_file)
    incomplete_jobs = df['COMPLETED' in df['State']]['JobID'].tolist()

    if incomplete_jobs:
        job_folder = os.path.dirname(report_file)
        move_incomplete_results(incomplete_jobs, job_folder, dry_run)
        make_incomplete_recordingSettingsCSV(incomplete_jobs, job_folder)

def move_incomplete_results(incomplete_jobs, job_folder, dry_run=False):
    results_dir = os.path.join(job_folder, 'results')
    failed_dir = os.path.join(job_folder, 'failed')
    if not os.path.exists(failed_dir):
        os.makedirs(failed_dir)
    result_folders = os.listdir(results_dir)
    for job_id in incomplete_jobs:
        matchingFolder =  [x for x in result_folders if x.endswith(job_id)]
        if len(matchingFolder)>1:
            print("more than 1 matching folder found for {job_id}, skipping")
            continue
        elif len(matchingFolder)==0:
            print(f'no matching folders found for {job_id}')
            continue
        else:
            folder_name = matchingFolder[0]

        src_folder = os.path.join(results_dir, folder_name)
        dest_folder = os.path.join(failed_dir, folder_name)
        moveMessage(src_folder,dest_folder)
    
        if dry_run:
            print('Dry-run, no files were actually moved')
        else:
            shutil.move(src_folder, dest_folder)

def make_incomplete_recordingSettingsCSV(incomplete_jobs, job_folder,dry_run=False):
    badInds = [int(j.split('_')[1])-1 for j in incomplete_jobs]
    recordingSettingsCSV = os.path.join(job_folder, 'recordingSettings.csv')
    df = pd.read_csv(recordingSettingsCSV)
    need_rerun = df.iloc[badInds]
    fname = f'recordingSettings_failed_{incomplete_jobs[0].split('_')[0]}.csv'
    fname = os.path.join(job_folder,fname)

    print('The follow job settings:')
    print(need_rerun)
    print('Will be written to:')
    print(fname)
    if dry_run:
        print(f'Dry-Run: CSV file not created')
    else:
        need_rerun.to_csv(fname, index=False)

def moveMessage(src_folder,dest_folder):
    print()
    print('Moving:')
    print(src_folder)
    print('to:')
    print(dest_folder)
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python cleanup.py <path_to_csv> [--dry-run]")
        sys.exit(1)
    
    status_csv = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    cleanup(status_csv, dry_run)