#!/usr/bin/env python

# File: udaily_csv.py
# Version: 0.1
# Date: 11 Nov 2008
# Author: Martin S. Ewing

#    udaily_csv.py extracts summaries from log files and appends to CSV file.
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

import os,os.path,sys

# Input for this program will be "FINDIR", since we are running after the fact
# to create the CSV file.
FINDIR = "logs/processed"    # Where to get logs
REPDIR = "reports"        # Where to put reports and plots and csv file
CSVOUT = "ulogs.csv"    # name of output file

def report(date,csvfd):        # report from log of given date, output fd for append
    ifn = FINDIR+"/ulog"+date+".log"
    ifd = open(ifn, 'r')    # open input log
    nsamples= nfurn= nhw= nz1= nz2= nz3 = 0    # accumulated time samples
    thw_min=tamb_min = 99.
    thw_max=tamb_max = -99.
    tamb_sum = 0.
    for line in ifd:    # Scan file to make print report
        # used fixed format decode of line
        try:
            hhmmss = line[:6]
            thw = float(line[7:12])
            fhw = int(line[13:14])
            ffurn = int(line[15:16])
            fz1 = int(line[17:18])
            fz2 = int(line[19:20])
            fz3 = int(line[21:22])
            tamb = float(line[23:])
        except ValueError:
            continue    # Don't count a bad line
        nsamples += 1
        thw_min = min(thw_min,thw)
        thw_max = max(thw_max,thw)
        tamb_min = min(tamb_min,tamb)
        tamb_max = max(tamb_max,tamb)
        tamb_sum += tamb
        if fhw :    nhw += 1
        if ffurn :  nfurn += 1
        if fz1 :    nz1 += 1
        if fz2 :    nz2 += 1
        if fz3 :    nz3 += 1
    durmin = 0.5*nsamples    # presumed minutes spanned
    durhr = durmin/60.0
    tav = tamb_sum / float(nsamples)
    print >>csvfd, \
        "%s, %.0f, %.1f, %.1f, %.1f, %.1f, %.1f, %.1f, %.1f, %.1f" % \
        (date,durmin,tamb_min,tamb_max,tav,nfurn/2.,nhw/2.,nz1/2.,nz2/2.,nz3/2.)
    ifd.close()

### MAIN ENTRY ###
csvn = REPDIR+"/"+CSVOUT
csvfd = open(csvn, 'w')     # A new CSV output file.
log_list = os.listdir(FINDIR)
log_list.sort()
for x in log_list:
    if x[-1] is "~":    # ignore any backups from vi, etc.
        continue
    date_part = x[4:12]    # YYYYMMDD
    print "Processing %s" % x
    report(date_part, csvfd)    # do the interesting stuff
csvfd.close()
