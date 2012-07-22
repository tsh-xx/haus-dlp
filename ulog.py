#!/usr/bin/env python

# File: ulog.py
# Version: 0.11
# Date: 19 Nov 2008
# Author: Martin S. Ewing

#    ulog.py captures and logs data from a DLP-IO8-G data acquisition unit.
#    Copyright (C) 2008 Martin S. Ewing
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# To do:
# separate event logs for each device?
# filter out "unchanged" entries?
# gzip old days' logs?

import time,serial,sys,os

INTERVAL = 30.0            # seconds between samples
DLP_DEV = "/dev/ttyUSB0"    # A/D device

# DLP-IO8-G codes, ports 1 - 8
DO_HI = ['1','2','3','4','5','6','7','8'] # set dig out high
DO_LO = ['Q','W','E','R','T','Y','U','I'] # set dig out low
DI    = ['A','S','D','F','G','H','J','K'] # read dig in
AI    = ['Z','X','C','V','B','N','M',','] # read analog in
TI    = ['9','0','-','=','O','P','[',']'] # read temp in
DLPASC= '`' # set ascii mode
DLPBIN= '\\' # set binary mode
DLPF  = 'L' # set fahrenheit
DLPC  = ';' # set celsius
DLPING= "'" # ping

# Store events (pumps on/off, etc) in separate file when they occur.
# Construct file names using current date.

date_string = time.strftime("%Y%m%d")
date_string_old = date_string
LOGFORMAT = "logs/ulog%s.log"
EVTFORMAT = "logs/uevt%s.log"
PENLOGFORMAT = "logs/pending/ulog%s.log"
LOGDIR = "logs"
REPTDIR = "reports"
PENDIR = "logs/pending" # where to put completed day's log
LOGBLEN = 128           # log buffer length
EVTBLEN = 0             # event buffer length
NTRY=3                  # Number of retries allowed for temps.
T_RETRY= 2.0            # wait time if retrying. (exptl)
T0 = 0.1                # spacing between temp. commands (exptl)
T1 = 0.1                # spacing between channels (exptl)
TEMP_INVAL = 39.99      # Temp. to use in case of wild reading (can't occur naturally)
NEG_MASK = -1 << 16     # for temp. sign correction

# Check validity of Dig. Input and invert sense.
def dio_decode(raw, id):
    if not raw in [chr(0), chr(1)]:
        print "ulog: invalid digital input [%s]: %d" \
            % (id, ord(raw))
        raw = chr(0)
    return 1 - ord(raw)

# return the time delay from now until next integral number of IVL seconds.
def until_next_interval(IVL):
    next_int = (IVL * (1.00+(time.time()//IVL))) + 0.001
    return next_int-time.time()

#### REAL ENTRY ####

# Open DLP-IO8-G device which appears as DLP_DEV
# Assume we have appropriate privilege.
try:
    ser = serial.Serial(DLP_DEV, 115200, timeout=1)
except serial.serialutil.SerialException:
    print "ulog: Can't open DLP-IO8-G on %s, terminating." % DLP_DEV
    sys.exit()

ser.write(DLPBIN)        # ensure binary mode

logfd = open(LOGFORMAT % date_string, 'a', LOGBLEN) # Open/append log file.
evtfd = open(EVTFORMAT % date_string, 'a', EVTBLEN) # record discrete events

hwc_state_old = -1        # hot water prev state
furn_state_old = -1        # furnace prev state
z1_state_old = -1        # zone 1
z2_state_old = -1        # zone 2
z3_state_old = -1        # zone 3
time_last_event = time.time()    # time of previous event (float sec) 

timestring = time.asctime()
print >>evtfd,      "%s --- Logging (re)started ---" % timestring
print >>sys.stderr, "%s --- Logging (re)started ---" % timestring

# start out on INTERVAL boundary.
time.sleep(until_next_interval(INTERVAL))

try:
  while (True):
    date_string = time.strftime("%Y%m%d")    # NB: date may have changed
    if date_string <> date_string_old:    # yes, new date
        logfd.close()            # close old logs, start new
        evtfd.close()
        print >>sys.stderr, "Date change, was %s, now %s" % \
            (date_string_old, date_string)
        old_name = LOGFORMAT % date_string_old        # move to
        new_name = PENLOGFORMAT % date_string_old    # pending dir.
        try:
            print >>sys.stderr, "Renaming %s to %s" % \
                (old_name, new_name)
            os.rename(old_name,new_name)    # awaiting report gen.
        except OSError:
            print >>sys.stderr, "Rename failed."
            pass        # if can't rename, leave it be.
        logsdir = os.listdir("logs")    # take care of uevt* files
        for x in logsdir:
            if x[:4] == "uevt":    # i.e. uevt*
                # Move to reports directory
                print >>sys.stderr, "Renaming %s" % x
                try:
                    os.rename(LOGDIR+"/"+x, REPTDIR+"/"+x)
                except OSError:
                    print >>sys.stderr, "Rename failed."
                    pass
        os.system("sudo ntpdate 1.pool.ntp.org")    # set clock
                                # since ntpd NG.
        date_string_old = date_string
        logfd = open(LOGFORMAT % date_string, 'a', LOGBLEN)
        evtfd = open(EVTFORMAT % date_string, 'a', EVTBLEN)    
    time_string = time.strftime("%H%M%S")
    time_now = time.time()

    # Read all inputs
    # Port 1 = Temperature (DHW Flow)
    for i in range(NTRY):    # Allow retries in case of blown reading
        ser.write(TI[1])
        time.sleep(T0)    # slowdown -> more reliable?
        t_raw = ser.read(2)
        # This temperature is always > 0...
        temp_hw = 0.0625 * (ord(t_raw[1]) << 8 | ord(t_raw[0]))
        if temp_hw < 70.:    # i.e., normal reading
            break
        time.sleep(T_RETRY)    # Try waiting a little
        ermsg = "%s HW Temp retry" % time_string
        print >>evtfd, ermsg
        print >>sys.stderr, ermsg
    if temp_hw > 70. : temp_hw = TEMP_INVAL  # could be disconnected probe?
    time.sleep(T1)        # slow down inter-port

    # Port 2 = HW Circulator on/off
    ser.write(DI[1])
    hwc_raw = ser.read(1)
    hwc_state = dio_decode(hwc_raw, "HW Circulator")
    if hwc_state <> hwc_state_old:    # an event is happening
        hwc_state_old = hwc_state
        dtime = (time_now - time_last_event) / 60.
        time_last_event = time_now
        print >>evtfd, "%s hwc=%d (%.1f)" % \
            (time_string,hwc_state,dtime)
    time.sleep(T1)        # slow down inter-port

    # Port 3 = Furnace burner on/off
    ser.write(DI[2])
    furn_raw = ser.read(1)
    furn_state = dio_decode(furn_raw, "Furnace")
    if furn_state <> furn_state_old:    # an event
        furn_state_old = furn_state
        dtime = (time_now - time_last_event) / 60.
        time_last_event = time_now
        print >>evtfd, "%s furnace=%d (%.1f)" % \
            (time_string,furn_state,dtime)
    time.sleep(T1)        # slow down inter-port

    # Port 4 = Zone 1 circulator (downstairs, south)
    ser.write(DI[3])
    z1_raw = ser.read(1)
    z1_state = dio_decode(z1_raw, "Zone 1")
    if z1_state <> z1_state_old:
        z1_state_old = z1_state
        dtime = (time_now - time_last_event) / 60.
        time_last_event = time_now
        print >>evtfd, "%s Zone1=%d (%.1f)" % \
            (time_string,z1_state,dtime)
    time.sleep(T1)        # slow down inter-port

    # Port 5 = Zone 2 circulator (downstairs, north)
    ser.write(DI[4])
    z2_raw = ser.read(1)
    z2_state = dio_decode(z2_raw, "Zone 2")
    if z2_state <> z2_state_old:
        z2_state_old = z2_state
        dtime = (time_now - time_last_event) / 60.
        time_last_event = time_now
        print >>evtfd, "%s Zone2=%d (%.1f)" % \
            (time_string,z2_state,dtime)
    time.sleep(T1)        # slow down inter-port

    # Port 6 = Zone 3 circulator (upstairs)
    ser.write(DI[5])
    z3_raw = ser.read(1)
    z3_state = dio_decode(z3_raw, "Zone 3")
    if z3_state <> z3_state_old:
        z3_state_old = z3_state
        dtime = (time_now - time_last_event) / 60.
        time_last_event = time_now
        print >>evtfd, "%s Zone3=%d (%.1f)" % \
            (time_string,z3_state,dtime)
    time.sleep(T1)        # slow down inter-port

        # Port 7 = Temperature (ASHP)
    for i in range(NTRY):
        ser.write(TI[0])
        time.sleep(T0)    # slowdown -> more reliable?
        ta_raw = ser.read(2)
        # This temperature can be < 0... must check sign
        rawt = ord(ta_raw[1]) << 8 | ord (ta_raw[0])
        if rawt & 0x8000:               # Check sign bit
            rawt = NEG_MASK | rawt      # making full precision neg. int.
        tempa_hw = 0.0625 * rawt
        if tempa_hw < 70.:    # normal condition
            break        # valid temp, probably
        time.sleep(T_RETRY)
        ermsg = "%s Amb. Temp. retry" % time_string
        print >>evtfd, ermsg
        print >>sys.stderr, ermsg
        if tempa_hw > 70. : tempa_hw = TEMP_INVAL

    # Print and log result
    logitem = "%s %.2f %d %d %d %d %d %.2f" % (time_string, temp_hw, 
        hwc_state, furn_state, z1_state, z2_state, z3_state, tempa_hw)
    print logitem
    print >>logfd, logitem
     # wait till next integral mult. of INTERVAL secs.
    time.sleep(until_next_interval(INTERVAL))

except KeyboardInterrupt:        # e.g., from kill -SIGINT <proc>
    pass                # graceful termination

# Close up files and terminate.
logfd.close()
evtfd.close()
ser.close()
