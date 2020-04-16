import asyncio

#import os

#import sys
#from time import strftime


#import serial
#import serial.aio as serial_asyncio



    
import asyncio
from argparse import ArgumentParser
from . import ctd
from . import ui as ctdsampler_ui

def main(graph):
    ########### MAIN #############
    desc="Selects serial device to use (default /dev/ttyUSB0)"
    parser = ArgumentParser(description=desc)
    parser.add_argument("-d", "--device", dest="device", default='/dev/ttyUSB0', metavar="SERIAL_DEVICE", help="Path to serial device")

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

    ui.graph = graph
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
