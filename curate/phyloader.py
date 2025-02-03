#!//N/u/lapishla/BigRed200/.conda/envs/phy2/bin/python
import sys, os
from phy.apps.template import template_gui

sorterOutput = sys.argv[1]

dat_path = sorterOutput + '/temp_wh.dat'
paramsPath = sorterOutput + '/params.py'
newparamsPath = sorterOutput + '/params_update.py'
def main():
    validatePaths()
    updateParams()
    template_gui(newparamsPath)

def validatePaths():
    print('Validating paths')
    if not os.path.isfile(paramsPath):
        raise FileNotFoundError(f"params.py file not found at {paramsPath}")
    if not os.path.isfile(dat_path):
        raise FileNotFoundError(f"temp_wh.dat file not found at {dat_path}")

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
