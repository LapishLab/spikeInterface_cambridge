# This file holds a function that creates probes using probe interface for Lapish lab recordings.

import numpy as np
import matplotlib.pyplot as plt

from probeinterface import Probe
import probeinterface as pi
from probeinterface.plotting import plot_probe

def probeCreator(animalName):
    print('Animal Name:',animalName)

    if animalName == 'NT2CAPCohort2Animal5':

        # Create channel positions (note: these are the positions of the contacts in terms of open ephys channel number, not probe channel number)
        positions = np.zeros((64, 2))
        positions[0] = 0, 90
        positions[1] = 0, 30
        positions[2] = 0, 0
        positions[3] = 0, 60
        positions[4] = 16.5, 15
        positions[5] = 216.5, 45
        positions[6] = 216.5, 105
        positions[7] = 16.5, 135
        positions[8] = 16.5, 75
        positions[9] = 16.5, 105
        positions[10] = 16.5, 45
        positions[11] = 216.5, 15
        positions[12] = 216.5, 135
        positions[13] = 200, 0
        positions[14] = 0, 120
        positions[15] = 216.5, 75
        positions[16] = 1016.5, 45
        positions[17] = 1000, 0
        positions[18] = 1000, 90
        positions[19] = 1000, 30
        positions[20] = 800, 0
        positions[21] = 1000, 60
        positions[22] = 800, 30
        positions[23] = 800, 150
        positions[24] = 1000, 120
        positions[25] = 800, 120
        positions[26] = 800, 90
        positions[27] = 1016.5, 15
        positions[28] = 800, 60
        positions[29] = 1016.5, 105
        positions[30] = 1016.5, 75
        positions[31] = 1016.5, 135
        positions[32] = 816.5, 15
        positions[33] = 616.5, 75
        positions[34] = 816.5, 105
        positions[35] = 616.5, 45
        positions[36] = 816.5, 75
        positions[37] = 616.5, 105
        positions[38] = 616.5, 15
        positions[39] = 816.5, 45
        positions[40] = 600, 90
        positions[41] = 600, 60
        positions[42] = 600, 120
        positions[43] = 600, 30
        positions[44] = 600, 0
        positions[45] = 600, 150
        positions[46] = 816.5, 135
        positions[47] = 616.5, 135
        positions[48] = 400, 90
        positions[49] = 200, 90
        positions[50] = 416.5, 45
        positions[51] = 416.5, 105
        positions[52] = 416.5, 135
        positions[53] = 416.5, 75
        positions[54] = 416.5, 15
        positions[55] = 400, 0
        positions[56] = 200, 60
        positions[57] = 400, 30
        positions[58] = 400, 150
        positions[59] = 200, 120
        positions[60] = 400, 120
        positions[61] = 200, 30
        positions[62] = 400, 60
        positions[63] = 200, 150
        print('Positions:',positions)


        # Create shank IDs (note: these are shank IDs in terms of open ephys channel number, not probe channel number)
        shank_ids = np.zeros((64))
        shank_ids[0] = 0
        shank_ids[1] = 0
        shank_ids[2] = 0
        shank_ids[3] = 0
        shank_ids[4] = 0
        shank_ids[5] = 1
        shank_ids[6] = 1
        shank_ids[7] = 0
        shank_ids[8] = 0
        shank_ids[9] = 0
        shank_ids[10] = 0
        shank_ids[11] = 1
        shank_ids[12] = 1
        shank_ids[13] = 1
        shank_ids[14] = 0
        shank_ids[15] = 1
        shank_ids[16] = 5
        shank_ids[17] = 5
        shank_ids[18] = 5
        shank_ids[19] = 5
        shank_ids[20] = 4
        shank_ids[21] = 5
        shank_ids[22] = 4
        shank_ids[23] = 4
        shank_ids[24] = 5
        shank_ids[25] = 4
        shank_ids[26] = 4
        shank_ids[27] = 5
        shank_ids[28] = 4
        shank_ids[29] = 5
        shank_ids[30] = 5
        shank_ids[31] = 5
        shank_ids[32] = 4
        shank_ids[33] = 3
        shank_ids[34] = 4
        shank_ids[35] = 3
        shank_ids[36] = 4
        shank_ids[37] = 3
        shank_ids[38] = 3
        shank_ids[39] = 4
        shank_ids[40] = 3
        shank_ids[41] = 3
        shank_ids[42] = 3
        shank_ids[43] = 3
        shank_ids[44] = 3
        shank_ids[45] = 3
        shank_ids[46] = 4
        shank_ids[47] = 3
        shank_ids[48] = 2
        shank_ids[49] = 1
        shank_ids[50] = 2
        shank_ids[51] = 2
        shank_ids[52] = 2
        shank_ids[53] = 2
        shank_ids[54] = 2
        shank_ids[55] = 2
        shank_ids[56] = 1
        shank_ids[57] = 2
        shank_ids[58] = 2
        shank_ids[59] = 1
        shank_ids[60] = 2
        shank_ids[61] = 1
        shank_ids[62] = 2
        shank_ids[63] = 1
        print('shank_ids:',shank_ids) 
        
    elif animalName == 'TestAnimal':

        # Create channel positions (note: these are the positions of the contacts in terms of open ephys channel number, not probe channel number)
        n = 64
        positions = np.zeros((n, 2))
        for i in range(n):
            x = i // 8
            y = i % 8
        positions[i] = x, y
        positions *= 20
        print('Positions:',positions)

        # Create the shank ids
        shank_ids = np.zeros(n)
        for i in range(n):
            shank_ids[i] = i // 6
        print('shank_ids:',shank_ids)  
    else:
        print('Invalid animal selection in probeCreator.')
    

    # Make the probe
    # probe = Probe(ndim=2, si_units='um')
    probe = pi.get_probe(manufacturer='cambridgeneurotech', probe_name='ASSY-158-F')
    print('Probe Attribues:',dir(probe))
    print('Default Positions:',probe._contact_positions)
    print('Default Shank IDs:',probe.shank_ids)
    print('Default Device Channel Indices:',probe.device_channel_indices)
    # probe.set_contacts(positions=positions, shapes='circle', shape_params={'radius': 5})
    probe.set_contacts(positions=positions)
    probe.set_shank_ids(shank_ids)

    # Set the device indices (Nick isn't sure what this does. Is this the difference between probe channels and open ephys channels?)
    probe.set_device_channel_indices(np.arange(64))

    # Show the probe
    plot_probe(probe,with_channel_index=True)
    plt.show()

    # Return the probe
    return probe