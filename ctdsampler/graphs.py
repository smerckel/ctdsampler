from collections import deque
from functools import partial

import multiprocessing as mp

import matplotlib.pyplot as plt
import numpy as np

import logging

logger = mp.log_to_stderr()
logger.setLevel(logging.CRITICAL)
#logger.setLevel(logging.INFO)

# Process Plotter, a cllas to plot data receiving from a pipe
# the methods plot_init and plot_update are to be subclassed.

class ProcessPlotter:
    def __init__(self, **options):
        self.options = options
        self.command_bindings = {}
        self.add_command_binding(command = 'close', callback=self.terminate, return_value=False)
        
    def plot_init(self):
        raise NotImplementedError()

    def plot_update(self, *p, **k):
        raise NotImplementedError()

    def plot_clear(self, *p, **k):
        raise NotImplementedError()
    
    def terminate(self):
        plt.close('all')

    def add_command_binding(self, command, callback, return_value=True):
        self.command_bindings[command] = (callback, return_value)
        
    def call_back(self):
        try:
            return_value = True
            while self.pipe.poll():
                data_type, payload = self.pipe.recv()
                if data_type=='command' and payload in self.command_bindings.keys():
                    func, return_value = self.command_bindings[payload]
                    func()
                elif data_type=="data":
                    logger.info("data")
                    self.plot_update(*payload, plot_type='lines')
                    self.fig.canvas.draw()
                    return_value = True
                else:
                    self.plot_update(*payload, plot_type='points')
                    self.fig.canvas.draw()
                    return_value = True

        except:
            logger.info("Callback error")
        return return_value
            
    def __call__(self, pipe):
        self.pipe = pipe
        self.plot_init()
        timer = self.fig.canvas.new_timer(interval=50)
        timer.add_callback(self.call_back)
        timer.start()
        plt.show()
        
def create_plot_process(plotter):
    ''' Factory function to create a plot_process and comms pipe for given plotter'''
    plot_pipe, plotter_pipe = mp.Pipe()
    plot_process = mp.Process(target=plotter,
                              args=(plotter_pipe,),
                              daemon=True)
    plot_process.start()
    return plot_process, plot_pipe


###############
# custom plotter
#
class FourPanelPlotter(ProcessPlotter):

    def __init__(self, **options):
        super().__init__(**options)
        self.add_command_binding('clear', self.plot_clear, True)
        self.add_command_binding('adjust_axes', self.plot_adjust_axes, True)
        self.add_command_binding('set_labels_raw', partial(self.plot_set_labels,'raw'), True)
        self.add_command_binding('set_labels_converted', partial(self.plot_set_labels,'converted'), True)
        
    def plot_update(self, *p, plot_type=None):
        if len(p)==6:
            c, t, d, dt, P, T = p
        else:
            c, t, d, P, T = p
            dt = None
        if plot_type=='lines':
            data = self.data
            artists = self.lines
        else:
            data = self.data_points
            artists = self.points
        data['P'].append(P)
        data['T'].append(T)
        data['c'].append(c)
        data['t'].append(t)
        data['d'].append(d)
        if not dt is None:
            data['dt'].append(dt)
        for p, artist in zip("c t d dt P T".split(), artists):
            y = np.array(data[p])
            x = np.arange(y.shape[0])
            artist.set_data(x,y)

    def plot_init(self):
        N = self.options['N']
        self.data = {'P' : deque(maxlen=N),
                     'T' : deque(maxlen=N),
                     'c' : deque(maxlen=N),
                     't' : deque(maxlen=N),
                     'd' : deque(maxlen=N),
                     'dt' : deque(maxlen=N)}
        self.data_points = {'P' : deque(maxlen=N),
                            'T' : deque(maxlen=N),
                            'c' : deque(maxlen=N),
                            't' : deque(maxlen=N),
                            'd' : deque(maxlen=N),
                            'dt' : deque(maxlen=N)}
        self.fig, self.ax = plt.subplots(6,1, sharex=True)
        self.lines = []
        self.points = []
        for p, ax in zip("c t d dt P T".split(), self.ax):
            line, = ax.plot([], label='Averaged', zorder=100)
            self.lines.append(line)
            points, = ax.plot([],'o', label='Measurement')
            self.points.append(points)

            ax.set_xlim(0,N)
            ax.relim()
            ax.autoscale_view()
            ax.legend(loc='upper left')
            
    def plot_clear(self):
        for d in self.data.values():
            d.clear()
        for d in self.data_points.values():
            d.clear()
            
    def plot_adjust_axes(self):
        for ax in self.ax:
            ax.relim()
            ax.autoscale(enable=True, axis='y')
            ax.set_autoscale_on(True)
            ax.set_xlim(0, self.options['N'])
            
    def plot_set_labels(self, label_type):
        for label, ax in zip(self.options['labels'][label_type], self.ax):
            ax.set_ylabel(label)

class Graph(object):
    def __init__(self, N=100):
        labels = dict(converted=["C (S/m)", "T (degC)", "P (bar)", "-", "Pinternal (Pa)", "Tinternal (degC)"],
                      raw=["P1 (counts)", "P2 (counts)", "P3 (counts)", "P4 (counts)", "Pinternal (Pa)", "Tinternal (degC)"])
        plotter = FourPanelPlotter(N=N, labels=labels)
        self.plot_process, self.plot_pipe = create_plot_process(plotter)
        self.is_labels_set = False

        
    def plot(self, *p):
        self.plot_pipe.send(('data',p))
        if not self.is_labels_set:
            self.is_labels_set=True
            if len(p)==5:
                self.set_labels('converted')

            elif len(p)==6:
                self.set_labels('raw')
            else:
                self.is_labels_set=False
                
    def plot_points(self, *p):
        self.plot_pipe.send(('data_points',p))
                
    def close(self):
        self.plot_pipe.send(('command', "close"))

    def clear(self):
        self.plot_pipe.send(('command', "clear"))
        
    def adjust_axes(self):
        self.plot_pipe.send(('command', 'adjust_axes'))

    def set_labels(self, label_type):
        self.plot_pipe.send(('command', 'set_labels_%s'%(label_type)))










