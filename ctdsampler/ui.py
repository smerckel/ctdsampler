import asyncio
from collections import deque
import urwid
import time

from . import graphs

_, QUIT, STOP, START, SAVE, CLEAR, TOGGLE_OUTPUT_FORMAT, GRAPH, ADJUST_AXIS = range(9)


class RunningAverager(object):
    ''' Running averaging class based on a recursive form of calculating 
        an average.
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
        self.israwoutput = False
        self.issaving = False
        self.ra = self.create_running_averagers()
        
    def create_widgets(self):
        text_top = urwid.Text(('top', u"\n"*(self.sizes['top']-1)))
        text_top_window = urwid.LineBox(text_top, title = u'Monitor')
        
        text_body = urwid.Text(('body', u'\n'*(self.sizes['body']-1)))
        text_body_window = urwid.LineBox(text_body, title = u'Results')

        s = [('bottom', u' '),
             ('button', u'A'), ('bottom', u': Adjust axes     '),
             ('button', u'S'), ('bottom', u': Stop logging    '),
             ('button', u'R'), ('bottom', u': Start logging   '),
             ('button', u'C'), ('bottom', u': Clear avgs      \n'),
             ('bottom', u' '),
             ('button', u'P'), ('bottom', u': Save cal params '),
             ('button', u'G'), ('bottom', u': Clear graph     '),
             ('button', u'O'), ('bottom', u': Toggle output   '),
             ('button', u'Q'), ('bottom', u': Quit            ')]

        text_bottom = urwid.Text(s)
        
        #text_bottom = urwid.Text(('bottom', u'S: Stop logging    R: Start logging   C: Clear averagers\nP: Save calibration params G: Toggle graph'))
        text_bottom_map = urwid.AttrMap(text_bottom, 'streak')
        text_bottom_padded = urwid.Padding(text_bottom_map, align='left', left=1, right=1)

        widgets = dict(monitor = text_top_window,
                       results = text_body_window,
                       menu = text_bottom_padded)
        scrolled_texts = dict(monitor = ScrolledText(self.sizes['top']),
                              results = ScrolledText(self.sizes['body']))
        return widgets, scrolled_texts

    def key_handler(self, key):
        action = None
        if key in ('q', 'Q'):
            action = QUIT
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
        elif key in ('A', 'a'):
            action = ADJUST_AXIS
        elif key in ('O', 'o'):
            action = TOGGLE_OUTPUT_FORMAT
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
            # see if we get a d,t,c triplet:
            try:
                data_in = [float(x) for x in s.split(',')]
            except ValueError:
                pass
            else:
                if len(data_in) == 3:
                    self.israwoutput = False
                    d, t, c = data_in
                    dt = None
                else:
                    d, t, c, dt = data_in
                    self.israwoutput = True
                self.islogging = True
                if self.israwoutput:
                    values = [self.ra[x].append(y) for x,y in zip('c t d dt'.split(),
                                                                  (c,t,d, dt))]
                else:
                    values = [self.ra[x].append(y) for x,y in zip('c t d'.split(),
                                                                  (c,t,d))]
                svalues = ["{:10.5f}".format(i) for i in values]
                m = self.scrolled_texts['results'].append(" ".join(svalues))
                self.widgets['results'].original_widget.set_text(m)
                self.graph.plot(*values)
                self.graph.plot_points(c, t, d, dt)

            
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
        return dict((k, RunningAverager()) for k in 'c t d dt'.split())

    def write_command(self, command):
        for c in command:
            self.writer(c)
        self.writer('\n')
        
    def command(self, action):
        if action == QUIT:
            self.graph.close()
            raise asyncio.CancelledError()
        elif action == CLEAR:
            for _, ra in self.ra.items():
                ra.reset()
            m = self.scrolled_texts['results'].clear()
            self.widgets['results'].original_widget.set_text(m)
        elif action == SAVE:
            if not self.islogging:
                self.write_command('dc')
        elif action == TOGGLE_OUTPUT_FORMAT and (self.islogging==False):
            self.write_command('')
            time.sleep(0.5)
            if self.israwoutput:
                self.write_command('OutputFormat=1')
                self.graph.set_labels('converted')
            else:
                self.write_command('OutputFormat=0')
                self.graph.set_labels('raw')
            self.israwoutput = not self.israwoutput
        elif action == STOP:
            self.islogging = False
            self.write_command('stop')
            self.write_command('\n')
        elif action == START:
            self.write_command('start')
        elif action == GRAPH:
            self.graph.clear()
        elif action == ADJUST_AXIS:
            self.graph.adjust_axes()
            
    def save_parameters_to_file(self, s):
        ''' Save calibration parameters to file with date time indication.'''
        fn = "{}.dat".format(strftime("%y%m%dT%H%M"))
        with open(fn, 'w') as fp:
            for l in s:
                fp.write("{}\n".format(l))

    
