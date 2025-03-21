#!//N/u/lapishla/BigRed200/.conda/envs/phy2/bin/python
import sys
from os.path import isfile

sorterOutput = sys.argv[1]
dat_path = sorterOutput + '/temp_wh.dat'
paramsPath = sorterOutput + '/params.py'
newparamsPath = sorterOutput + '/params_update.py'

def main():
    if '--clear-state' in sys.argv:
        clear_state()
    from phy.apps.template import template_gui
    if validatePaths():
        updateParams()
        template_gui(newparamsPath)
    else:
        print('Skipping params.py update. Phy might be able to use raw data (does not seem to work for KS4 sorted data).')
        template_gui(paramsPath)

def clear_state():
    from pathlib import Path
    global_state_file = str(Path.home()) + '/.phy/TemplateGUI/state.json'
    local_state_file = sorterOutput + '/.phy/state.json'
    if isfile(global_state_file):
        print('Removing global state file')
        # os.remove(global_state_file)
    else:
        print('Global state file not found in ', global_state_file)
    if isfile(local_state_file):
        print('Removing local state file')
        # os.remove(local_state_file)
    else:
        print('Local state file not found ', local_state_file)

def validatePaths():
    print('Validating paths')
    if not isfile(paramsPath):
        raise FileNotFoundError(f"params.py file not found at {paramsPath}")
    if not isfile(dat_path):
        print(f"temp_wh.dat file not found at {dat_path}")
        return False
    return True

def updateParams():
    print('Updating dat_path in params_update.py') 
    lines = []
    with open(paramsPath, 'r') as file:
        lines = file.readlines()

    for i,line in enumerate(lines):
        if line.startswith('dat_path'):
            lines[i] = f"dat_path = '{sorterOutput}/temp_wh.dat'\n"
    with open(newparamsPath, 'w') as file:
        file.writelines(lines)

if __name__ == "__main__":
    main()
