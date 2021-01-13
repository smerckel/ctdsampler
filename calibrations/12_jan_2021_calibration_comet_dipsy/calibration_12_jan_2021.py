from matplotlib import pyplot as plt
import numpy as np

from ctdsampler import calibration

# uncomment to input data manually.

#dinput = KeyboardInput()
#dinput.input_by_keyboard()
#dinput.save_data()

comet = calibration.ConductivityCalibration()
comet.load_data('comet_ctd_calibration_12_jan_2021.txt')
coefs0 = np.array([-9.815294e-1, 1.442087e-1, -2.650806e-4, 4.065385e-5])
comet.calibrate(coefs0=coefs0)

dipsy = calibration.ConductivityCalibration()
dipsy.load_data('dipsy_ctd_calibration_21_jan_2012.txt')
dipsy.calibrate(coefs0=coefs0)

with open('comet_ctd_coefs_12_jan_2021.txt', 'w') as fp:
    comet.report('comet', fp)
with open('dipsy_ctd_coefs_12_jan_2021.txt', 'w') as fp:
    dipsy.report('dipsy', fp)
    
f, ax = comet.graph('comet')
f, ax = dipsy.graph('dipsy', f, ax)

plt.show()
