import asyncio

#import os

#import sys
#from time import strftime


#import serial
#import serial.aio as serial_asyncio



    
import asyncio
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import multiprocessing as mp

from . import ctd
from . import ui as ctdsampler_ui
from . import graphs

def main():
    mp.set_start_method('spawn')
    
    ########### MAIN #############
    desc='''
    CTD SAMPLER
    -----------
    
    The program ctdsampler is a utility that allows reading out
    Seabird's Glider Payload CTDs.

    Wiring
    ------

    The CTD is to be connected to a serial port on this computer:

    +----------------------------------------------------------------+
    | PC -> switch board : 3 wired serial cable (RX/TX/GND)          |
    |                                                                |
    | switch board -> CTD : 4 wired serial cable (RX/TX/VCC/GND)     |
    |                                                                |
    | power source -> switch board : 2 wired power cable (VCC/GND)   |
    +----------------------------------------------------------------+

    The voltage supply to the CTD should be betwen 8 and 20 V. Do not
    overload!

    Operation
    ---------
    When the program is started, it shows two data fields: Monitor and
    Results.  The Monitor field shows the output from the CTD as read
    by the program. When the CTD is logging, then triplet or
    quadruplets of data are shown, depending on the setting of the
    output format (raw (4) or converted (3)).  In case of converted
    data (3 values), the colums indicate conductivity, temperature and
    pressure, respectively.

    The Results field shows the running averaged values of the data
    read.

    When the program is started, also a graphic window pops-up,
    showing the data recorded graphically. Measurements (values
    presented in Monitor) are indicated by a dot, whereas the running
    averages (values presented in Results) are shown as lines.
    Depending on the output format (raw/converted), four or three
    panels are populated with data.

    Commands
    
    Note: The key commands to the program work only if the terminal
    window is active!

    +----------------------------------------------------------------------+
    | Stop and Start logging : press S and R, respectively                 |
    |                                                                      |
    | Change output format   : CTD should not be logging (press S first).  |
    |                          Type O to toggle the format.                |
    |                                                                      |
    | Reset running averaged : press C (when logging). The averagers of for|
    |                          the values in                               |
    |                          the Result field are reset. Also applies to |
    |                          the graphical representation                |
    |                                                                      |
    | Clear graph            : press G to erase all data from the graphs   |
    |                                                                      |
    | Adjust y-scales        : press A to adjust the y-scales of all graphs|
    |                          to the data extent.                         |
    |                                                                      |
    | End program            : press Q                                     |
    +----------------------------------------------------------------------+

    
    Bugs
    ----
    Closing the graphical window causes the program to exit uncleanly.

    '''
    parser = ArgumentParser(description=desc,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--device", dest="device", default='/dev/ttyUSB0', metavar="SERIAL_DEVICE", help="Path to serial device")
    parser.add_argument("-N", "--data_buffer_size", dest="data_buffer_size", default=100, type=int)
    
    options = parser.parse_args()

    device = options.device
    baudrate = 9600
    # get the event loop and queue to pass data from ctd_interface to ui
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()


    # and the ctd_interface (serial connection to the CTD itself)
    ctd_interface = loop.run_until_complete(ctd.start_serial_interface(loop, queue,
                                                                       ctd.CTDInterface,
                                                                       device, baudrate))
        
    # create the user interface.
    ui = ctdsampler_ui.UI(loop, queue)
    # connect ctd_interface.writer to ui.writer
    ui.writer = ctd_interface.writer
    # 
    urwid_loop = ui.build_app()

    ui.graph = graphs.Graph(options.data_buffer_size)
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
    #plt.close('all') # Who creates the figure???
    return 0
