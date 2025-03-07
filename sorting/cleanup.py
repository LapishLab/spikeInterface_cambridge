from os import makedirs, listdir, path
import sys
from shutil import move
import pandas as pd

def cleanup(report_file, output_folder, dry_run=False):
    job_folder = path.dirname(report_file)
    rec_setting_path = job_folder + '/recordingSettings.csv'
    rec_settings = pd.read_csv(rec_setting_path)
    output_subfolders = listdir(output_folder)
    report = pd.read_csv(report_file)

    rec_settings['output_path'] = ''
    rec_settings['state'] = ''
    for (i, row) in report.iterrows():
        id = row['Array Job ID'].strip()
        matchingFolder =  [x for x in output_subfolders if x.endswith(id)]
        if len(matchingFolder)>1:
            print(f"more than 1 matching folder found for {id}, skipping")
            continue
        elif len(matchingFolder)==0:
            print(f'no matching folders found for {id}')
            continue
        else:
            output_path = f'{output_folder}/{matchingFolder[0]}'
            rec_ind = int(id.split('_')[1]) - 1
            if 'COMPLETED' in row['State']:
                rec_settings.loc[rec_settings.index[rec_ind], 'state'] = 'COMPLETED'
            else:
                rec_settings.loc[rec_settings.index[rec_ind], 'state'] = 'FAILED'
                failed_output_path = f'{output_folder}/failed/{matchingFolder[0]}'
                makedirs(f'{output_folder}/failed/', exist_ok=True)
                move(output_path,failed_output_path)
                output_path = failed_output_path
            rec_settings.loc[rec_settings.index[rec_ind], 'output_path'] = output_path
    job_num = id.split('_')[0].strip()
    completed = rec_settings[rec_settings['state'] == 'COMPLETED']
    if not completed.empty:
        completed.to_csv(f'{job_folder}/recordingSettings_completed_{job_num}.csv', index=False)
    failed = rec_settings[rec_settings['state'] == 'FAILED']
    if not failed.empty:
        failed.to_csv(f'{job_folder}/recordingSettings_failed_{job_num}.csv', index=False)
        

if __name__ == "__main__":    
    report_file = sys.argv[1]
    output_folder = sys.argv[2]
    cleanup(report_file, output_folder)