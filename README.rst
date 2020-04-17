# ctdsampler
CTDsampler program

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
