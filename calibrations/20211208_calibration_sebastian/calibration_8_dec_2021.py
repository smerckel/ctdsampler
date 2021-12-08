from matplotlib import pyplot as plt
import numpy as np

from ctdsampler import calibration

# uncomment to input data manually.

#dinput = KeyboardInput()
#dinput.input_by_keyboard()
#dinput.save_data()

sebastian = calibration.ConductivityCalibration()
sebastian.load_data('sebastian_ctd_calibration_8_dec_2021.txt')
coefs0 = np.array([-9.815294e-1, 1.442087e-1, -2.650806e-4, 4.065385e-5])
sebastian.calibrate(coefs0=coefs0)


with open('sebastian_ctd_coefs_8_dec_2021.txt', 'w') as fp:
    sebastian.report('sebastian', fp)
    
f, ax = sebastian.graph('sebastian')

plt.show()
