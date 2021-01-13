import sys
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import fmin
from collections import namedtuple

# bath_temp bath_cond inst_freq
# degree C  S/m       Hz

Coefs = namedtuple('Coefs', 'g h i j'.split())

class KeyboardInput(object):
    def __init__(self):
        self.bath_temp = []
        self.bath_cond = []
        self.inst_freq = []

    def input_by_keyboard(self):
        print("Enter data, white space delimited for:")
        print("bath_temp, bath_cond and inst_freq (degree C, S/m, Hz).")

        while True:
            ans = input("> ").strip()
            if ans == 'q':
                break
            try:
                tmp = ans.strip().split()
                bath_temp, bath_cond, inst_freq = [float(i) for i in tmp]
            except Exception:
                print("Failed to interpret data.")
            else:
                self.bath_temp.append(bath_temp)
                self.bath_cond.append(bath_cond)
                self.inst_freq.append(inst_freq)
        print("Done inputing data")

    def save_data(self):
        ans = input("Enter output filename : ")
        with open(ans, 'w') as fp:
            fp.write("# bath_temp bath_cond inst_freq\n")
            fp.write("# degree C  S/m       Hz\n")
            fp.write("#\n")
            for i0, i1, i2 in zip(self.bath_temp,
                                  self.bath_cond,
                                  self.inst_freq):
                s = f"{i0} {i1} {i2}\n"
                fp.write(s)
        print("Data saved.")
                     
    
    
class ConductivityCalibration(object):
    def __init__(self):
        self.WBOTC = 4.7841e-7
        self.CPcor = -9.57e-8
        self.CTcor = 3.25e-5
        self.bath_temp = []
        self.bath_cond = []
        self.inst_freq = []
        
    def load_data(self, filename):
        with open(filename, 'r') as fp:
            while line:=fp.readline():
                if line.strip().startswith("#"):
                    continue
                else:
                    bath_temp, bath_cond, inst_freq = [float(i) for i in line.split()]
                    self.bath_temp.append(bath_temp)
                    self.bath_cond.append(bath_cond)
                    self.inst_freq.append(inst_freq)

    def conductivity(self, f, t, p, coefs, delta, epsilon):
        g,h, i, j = coefs
        C = (g + h*f**2 + i*f**3 + j*f**4)/(1+delta*t + epsilon*p)
        return C

    def cost_fun(self, coefs, C, f, t, p, delta, epsilon):
        g,h, i, j = coefs
        coefs = self.normalise_coefs(coefs, reverse=True)
        Csensor = self.conductivity(f, t, p, coefs, delta, epsilon)
        cost = ((Csensor-C)**2).sum()
        return cost
    
    def normalise_coefs(self, coefs, reverse=False):
        factors = np.array([1, 1e-1, 1e-4, 1e-5])
        if reverse:
            factors = 1/factors
        coefs = [i/j for i,j in zip(coefs, factors)]
        return coefs

    @property
    def f(self):
        f = np.array(self.inst_freq) * np.sqrt(1.0 + self.WBOTC)/1000.0
        return f

    def calibrate(self, coefs0 = [-9.815294e-1, 1.442087e-1, -2.650806e-4, 4.065385e-5]):
        f = self.f
        C = np.array(self.bath_cond)
        t = np.array(self.bath_temp)
        delta = self.CTcor
        epsilon = self.CPcor
        p = np.zeros_like(t)
        coefs = self.normalise_coefs(coefs0)
        coefs = fmin(self.cost_fun, coefs, args=(C, f, t, p, delta, epsilon),
                     xtol=1e-7, ftol=1e-8, maxiter=100000, disp=0)
        coefs = self.normalise_coefs(coefs, reverse=True)
        Csensor = self.conductivity(f, t, p, coefs, delta, epsilon)
        residuals = C-Csensor
        self.coefs = Coefs(*coefs)
        self.residuals = residuals
        self.Csensor = Csensor

    def report(self, glider, fp=None):
        if not fp is None:
            self.__report(glider, fp)
        self.__report(glider, sys.stdout)
            
    def __report(self, glider, fp):
        s = f"Calibration coefficients {glider.capitalize()}:\n"
        fp.write(s)
        fp.write("-"*len(s)+'\n')
        fp.write(f"g : {self.coefs.g}\n")
        fp.write(f"h : {self.coefs.h}\n")
        fp.write(f"i : {self.coefs.i}\n")
        fp.write(f"j : {self.coefs.j}\n")
        fp.write("\n")

    def graph(self, glider,  f=None, ax=None):
        if f is None or ax is None:
            f, ax = plt.subplots(2,1,sharex=True)
        ax[0].plot(self.bath_cond, label=f'Bath conductivity ({glider})')
        #ax[0].plot(self.Csensor, label=f'Sensor conductivity ({glider})')
        ax[1].plot(self.residuals, label=glider.capitalize())
        ax[0].set_ylabel('Conductivity (S/m)')
        ax[1].set_ylabel('Residual (S/m)')
        ax[1].set_xlabel('Measurement number')
        ax[1].set_ylim(-1e-3, 1e-3)
        ax[0].legend()
        ax[1].legend()
        return f, ax
