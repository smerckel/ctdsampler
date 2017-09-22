import asyncio
from collections import deque
import os
from optparse import OptionParser
import sys
from time import strftime
import warnings

import urwid
import matplotlib.pyplot as plt
import serial
import serial.aio as serial_asyncio


# plt.show(block=False) produces a warning. Ignore this from being printed.
warnings.filterwarnings("ignore", module="matplotlib")


_, STOP, START, SAVE, CLEAR, GRAPH = range(6)

class RunningAverager(object):
    ''' Running averaging class based on a recursive form of calculating 
        an averaged.
    '''
    def __init__(self):
        self.reset()
        
    def reset(self):
        ''' Resets the memory of the averaged. '''
        self.k = 0
        self.xp = 0.

    def append(self, z):
        ''' Append a new measurement

        Parameters:
        ----------
        z: measurement 

        Returns:
        --------
        the current estimate of the average.
        '''
        self.k+=1
        self.xp =self.xp + 1/self.k*(z - self.xp)
        return self.xp
    
    
class ScrolledText(object):
    ''' A simple buffer to a strings to. The buffer holds upto a given
        number of strings. 
    '''
    def __init__(self, size):
        ''' Constructor

        Params:
        -------
        size: sets the size of the buffer.
        '''
        self.size = size
        self.deque = deque([], self.size)
        self.clear()

    def append(self, s):
        ''' Append a string 

        Params:
        -------
        s: string

        Returns:
        A string with new line characters
        '''
        self.deque.append(s)
        return "\n".join(self.deque)

    def clear(self):
        '''
        Clears the buffer and returns an empty one.
        '''
        for i in range(self.size):
            self.deque.append("")
        return "\n".join(self.deque)
    
class Graph(object):
    ''' An interface to plot data in a 2D graph.
    
    This object is taylored to display conductivity data in a 3 panel graph,
    with predined y_lims() and y_labels.
    '''
    def __init__(self):
        self.i = 0
        self.x = []
        self.c = []
        self.t = []
        self.d = []
        self.curves = None
        self.colours = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        self.ylabels = ['C (S/m)',
                        'T (deg C)',
                        'P (bar)']
        self.ylimits = [(0,5), (0,25), (0,1)]
        
    def create_new(self):
        ''' Create a new figure '''
        self.f, self.ax = plt.subplots(3,1, sharex=True)
        self.i = 0
        self.x = []
        self.c = []
        self.t = []
        self.d = []
        self.curves = None
        
    def show(self):
        ''' Show the figure to the screen in a non-blocking fashion'''
        self.create_new()
        plt.show(block=False) 

    def close(self):
        ''' Close the figure '''
        plt.close(self.f)
        
    def plot(self, c, t, d):
        ''' Add a data triplet to the plot. The x range is updated automatically 
        
        Params:
        ------
        c: conductivity value (float)
        t: tempareture value (float)
        d: pressure value (float)
        '''
        self.x.append(self.i)
        self.c.append(c)
        self.t.append(t)
        self.d.append(d)
        self.i+=1
        # create one line per panel, and update the xdata/ydata.
        if not self.curves:
            self.curves = [_ax.plot(self.x, y, color=c)[0]
                           for _ax, y, c in zip(self.ax, (self.c, self.t, self.d),
                                                self.colours)]
            for _ax, lbl, limits in zip(self.ax, self.ylabels, self.ylimits):
                _ax.set_ylabel(lbl)
                _ax.set_ylim(*limits)
        else:
            for curve, y in zip(self.curves, (self.c,self.t,self.d)):
                curve.set_data(self.x, y)
            self.ax[-1].set_xlim(0, self.i)
        # make the loop to pause so that other things can happen.
        plt.pause(0.1)
        
class UI(object):
    '''
    A text User Interface, sporting a monitor window, a results window and a 
    menu/command window.
    '''
    palette = [('top', 'black', 'light gray'),
               ('body', 'black', 'dark red'),
               ('bottom', 'yellow', 'dark blue'),
               ('streak', 'yellow', 'dark blue'),
               ('button','white', 'dark blue')]
    # define the sizes of each window.
    sizes = dict(top=3, body=15, bottom=2)

    def __init__(self, loop, queue):
        self.loop = loop
        self.queue = queue
        self.islogging = False
        self.isplotting = False
        self.issaving = False
        self.ra = self.create_running_averagers()
        
    def create_widgets(self):
        text_top = urwid.Text(('top', u"\n"*(self.sizes['top']-1)))
        text_top_window = urwid.LineBox(text_top, title = u'Monitor')
        
        text_body = urwid.Text(('body', u'\n'*(self.sizes['body']-1)))
        text_body_window = urwid.LineBox(text_body, title = u'Results')

        s = [('bottom', u'    '),
             ('button', u'S'), ('bottom', u': Stop logging    '),
             ('button', u'R'), ('bottom', u': Start logging   '),
             ('button', u'C'), ('bottom', u': Clear avgs      \n'),
             ('bottom', u'    '),
             ('button', u'P'), ('bottom', u': Save cal params '),
             ('button', u'G'), ('bottom', u': Toggle graph    '),
             ('button', u'Q'), ('bottom', u': Quit            ')]

        text_bottom = urwid.Text(s)
        
        #text_bottom = urwid.Text(('bottom', u'S: Stop logging    R: Start logging   C: Clear averagers\nP: Save calibration params G: Toggle graph'))
        text_bottom_map = urwid.AttrMap(text_bottom, 'streak')
        text_bottom_padded = urwid.Padding(text_bottom_map, align='left', left=5, right=5)

        widgets = dict(monitor = text_top_window,
                       results = text_body_window,
                       menu = text_bottom_padded)
        scrolled_texts = dict(monitor = ScrolledText(self.sizes['top']),
                              results = ScrolledText(self.sizes['body']))
        return widgets, scrolled_texts

    def key_handler(self, key):
        action = None
        if key in ('q', 'Q'):
            raise asyncio.CancelledError()
        elif key in ('s', 'S'):
            action = STOP
        elif key in ('R', 'r'):
            action = START
        elif key in ('C', 'c'):
            action = CLEAR
        elif key in ('P', 'p'):
            action = SAVE
        elif key in ('G', 'g'):
            action = GRAPH
        else:
            pass
        if action:
            self.loop.call_soon(self.command, action)
        
    def build_top(self, widgets):
        top = urwid.Pile([ ('pack', widgets['monitor']),
                           ('pack', widgets['results']),
                           ('pack', widgets['menu'])])
        return top

    def build_app(self):
        widgets, scrolled_texts = self.create_widgets()
        top = self.build_top(widgets)
        evl = urwid.AsyncioEventLoop(loop=self.loop)
        urwid_loop = urwid.MainLoop(top, self.palette, event_loop=evl, unhandled_input = self.key_handler, handle_mouse = False)
        self.widgets = widgets
        self.scrolled_texts = scrolled_texts
        self.graph = Graph()
        return urwid_loop

    async def parse_input(self):
        ''' Input parser. A asyncio coroutine, that waits for data to arrive
            on the queue, and processes them accordingly.
        '''
        temp_list = []
        while True:
            try:
                s = await self.queue.get()
            except asyncio.CancelledErrror:
                break
            m = self.scrolled_texts['monitor'].append(s.rstrip())
            self.widgets['monitor'].original_widget.set_text(m)
            # see if we get a c,t,d triplet:
            try:
                c, t, d = [float(x) for x in s.split(',')]
            except ValueError:
                pass
            else:
                self.islogging = True
                values = [self.ra[x].append(y) for x,y in zip('c t d'.split(),
                                                              (c,t,d))]
                svalues = ["{:10.5f}".format(i) for i in values]
                m = self.scrolled_texts['results'].append(" ".join(svalues))
                self.widgets['results'].original_widget.set_text(m)
                if self.isplotting:
                    self.graph.plot(*values)
            
            # see if user requested to print calibration data.
            if "SBE Slocum Payload CTD" in s:
                self.issaving=True
                self.scrolled_texts['results'].clear()

            if self.issaving:
                temp_list.append(s)
                if 'POFFSET' in s:
                    self.save_parameters_to_file(temp_list)
                    self.issaving=False
                    if len(temp_list)%2:
                        temp_list.append("")
                    for v in zip(temp_list[::2], temp_list[1::2]):
                        m = self.scrolled_texts['results'].append("%35s %35s"%(v))
                    self.widgets['results'].original_widget.set_text(m)
                    temp_list.clear()
                

    def create_running_averagers(self):
        ''' create running averagers for c t and d variables.'''
        return dict((k, RunningAverager()) for k in 'c t d'.split())

    def write_command(self, command):
        for c in command:
            self.writer(c)
            
    def command(self, action):
        if action == CLEAR:
            for _, ra in self.ra.items():
                ra.reset()
            m = self.scrolled_texts['results'].clear()
            self.widgets['results'].original_widget.set_text(m)
        elif action == SAVE:
            if not self.islogging:
                self.write_command('dc\n')
                
        elif action == STOP:
            self.islogging = False
            self.write_command('stop\n')
            
        elif action == START:
            self.write_command('start\n')
        elif action == GRAPH:
            self.isplotting = not self.isplotting
            if self.isplotting:
                self.graph.show()
            else:
                self.graph.close()
                
    def save_parameters_to_file(self, s):
        ''' Save calibration parameters to file with date time indication.'''
        fn = "{}.dat".format(strftime("%y%m%dT%H%M"))
        with open(fn, 'w') as fp:
            for l in s:
                fp.write("{}\n".format(l))

class CTDInterface(asyncio.Protocol):
    RETURN = '\r\n'

    def __init__(self, *p, **k):
        super().__init__(*p, **k)
        self.buf = ''
                        
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        s = []
        for i in data:
            if i<255:
                s.append(chr(i))
        self.consume("".join(s))

    def connection_lost(self, exc):
        asyncio.get_event_loop().stop()
        
    def writer(self, mesg):
        mesg = mesg.replace("\n","\r\n")
        self.transport.write(mesg.encode())

    def consume(self, s):
        self.buf+=s
        if self.RETURN in self.buf:
            buf = self.buf.split(self.RETURN)
            n = len(buf) - int(not self.buf.endswith(self.RETURN))
            for i in range(n):
                _buf = buf.pop(0)
                if _buf:
                    self.queue.put_nowait(_buf)
            self.buf = ''.join(buf)
            

# a coroutine to start up the serial interface.
async def start_serial_interface(loop, queue, interface, port, baudrate):
    coro = serial_asyncio.create_serial_connection(loop, interface,
                                                   port, baudrate=9600)
    transport, protocol = await coro
    protocol.loop = loop
    protocol.queue = queue
    return protocol


def main():
    ########### MAIN #############
    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", default='/dev/ttyUSB0',
                      help="Selects serial port to use (default /dev/ttyUSB0)", metavar="SERIAL_PORT")

    (options, args) = parser.parse_args()

    port = options.port
    baudrate = 9600

    # get the event loop and queue to pass data from ctd_interface to ui
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()


    # and the ctd_interface (serial connection to the CTD itself)
    ctd_interface = loop.run_until_complete(start_serial_interface(loop, queue,
                                                                   CTDInterface,
                                                                   port, baudrate))
    # create the user interface.
    ui = UI(loop, queue)
    # connect ctd_interface.writer to ui.writer
    ui.writer = ctd_interface.writer
    # 
    urwid_loop = ui.build_app()

    # create tasks that are run asynchronously:
    tasks ={}
    tasks['input'] = loop.create_task(ui.parse_input())

    try:
        urwid_loop.run()
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass

    # clean up. Cancel tasks, stop urwid and close figure.
    for k, v in tasks.items():
        v.cancel()
    urwid_loop.stop()
    plt.close('all')
    return 0
