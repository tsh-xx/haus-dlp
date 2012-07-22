#!/usr/bin/env python

# File: uweb.py
# Version: 0.1
# Date: 20 Oct 2008
# Author: Martin S. Ewing

#    uweb.py runs daily to generate html pages from reports/logs/notes.
#    May run after (or as part of) udaily.py
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
# 

import os,os.path,sys,string

# Input files, one each per day:
# 1. log files - detailed record of temps and on/off values
# 2. plot files (png) - graphical summary of day
# 3. report files - Statistical analysis of day's data
# 4. note files - Any text notes added manually to explain day's results

# Output files
# 1. index.html updated to include link to following
# 2. daily html, which includes all of above reports in a pleasant format.

# log & report & html day files are named <prefix>YYYYMMDD<postfix>

HTTPLINK = "/uapp"          # in htdocs

FINDIR = "logs/processed"   # Where the logs will finish up
FINPRE = "ulog"             #    prefix for file name
FINEXT = ".log"             #    postfix (.extension)

REPDIR = "reports"          # Where to put reports and plots
REPPRE_PLOT = "plot"        #    prefix for plots
REPEXT_PLOT = ".png"        #    postfix
REPPRE_REP = "rept"         #    prefix for text report
REPEXT_REP = ".txt"         #    postfix

NOTESDIR = "notes"          # Text notes location
NOTESPRE = "n"              #    prefix for note file
NOTESEXT = ".ext"           #    postfix

HTMLDIR = "html"            # Where the generated html goes
HTMLPRE = "h"               #    prefix for html day file
HTMLEXT = ".html"           #    postfix

ndir = os.listdir(NOTESDIR) # List of notes files (.txt)
rdir = os.listdir(REPDIR)   #    reports files (.png and .txt)
ldir = os.listdir(FINDIR)   #    finished logs (.log)
hdir = os.listdir(HTMLDIR)  # HTML files (before this run)

# Generate html for "prev -- up -- next" links
def write_prev_up_next(dayhtmlf, idate, to_process):
    dayhtmlf.write('<p>[')
    if idate > 0:                                       # make "prev"
        dayhtmlf.write(' <a href="%s">prev</a>' % 
            (HTMLPRE + to_process[idate-1] + HTMLEXT,))
    else:
        dayhtmlf.write('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')    # for first item
    dayhtmlf.write(' -- <a href="/uapp/html/index.html">up</a> -- ')
    if idate < len(to_process)-1:                       # make "next"
        dayhtmlf.write('<a href="%s">next</a> ]</p>\n' % 
            (HTMLPRE + to_process[idate+1] + HTMLEXT,))
    else:
        dayhtmlf.write('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;]</p>\n')  # last item

# canned header & trailer HTML files
HEADER = "day_header.html"
TRAILER = "day_trailer.html"
IXHEADER = "ix_header.html"
IXTRAILER = "ix_trailer.html"

plotdir = []
repdir = []
for x in rdir:              # find the plots & reports in REPDIR
    if x.startswith(REPPRE_PLOT):
        plotdir.append(x)
    elif x.startswith(REPPRE_REP):
        repdir.append(x)

# remove all files in output directory
for x in hdir:
    os.remove(os.path.join(HTMLDIR,x))
    
# Open the html index file.
ixf = open(os.path.join(HTMLDIR,"index.html"),'w')

# Initialize it from the header file.
ixhdf = open(IXHEADER,'r')
for line in ixhdf:
    ixf.write(line)
ixhdf.close()

# Our job is to create an html file for every finished log entry, i.e., each
# file in ldir.

to_process = []
for x in ldir:
    if not x.startswith(FINPRE):    # only look at ulog files
        continue
    fname, ext = os.path.splitext(x)
    if ext <> FINEXT:               # and ignore non-.log files if any
        continue
    fdate = fname.lstrip(string.ascii_letters)  # numeric date string yyyymmdd
    to_process.append(fdate)    # i.e. make list of dates to be handled
    to_process.sort()           # ensure alpha order

for idate in range(len(to_process)):    # use index to help with prev/next ptrs
    fdate = to_process[idate]
    # make a more readable date string
    fdate_expanded = "%s/%s/%s" % (fdate[:4], fdate[4:6], fdate[-2:])
    print "%s" % fdate_expanded

    # create the html page
    # open header & trailer canned html files
    headerf = open(HEADER,'r')
    trailerf = open(TRAILER,'r')
    # open html output file
    dayhtmlfn = os.path.join(HTMLDIR,HTMLPRE + fdate + HTMLEXT)
    dayhtmlf = open(dayhtmlfn, 'w')
    for line in headerf:
        dayhtmlf.write(line)    # copy header to new file
    dayhtmlf.write('\n')        # in case header did not have final newline
    headerf.close()
    # write prev, up, next links
    write_prev_up_next(dayhtmlf, idate, to_process)
    # write statistics text, if available
    for y in repdir:
        if y.find(fdate) > -1:              # found it
            statsf = open(os.path.join(REPDIR,y), 'r')
            dayhtmlf.write("<pre>\n")       # preformatted
            for line in statsf:
                dayhtmlf.write(line)        # copy statsfile
            dayhtmlf.write("</pre>\n")      # close preformatted
            statsf.close()
            break
    # write note text, if available
    for y in ndir:
        if y.find(fdate) > -1:              # found a note
            notef = open(os.path.join(NOTESDIR,y), 'r')
            dayhtmlf.write("<pre>Note:\n")       # preformatted
            for line in notef:
                dayhtmlf.write(line)
            dayhtmlf.write("</pre>\n")      # close preformatted
            notef.close()
            break
    # insert plot, if available
    for y in plotdir:
        if y.find(fdate) > -1:              # found a plot, incl image
            dayhtmlf.write('<img src="%s" />\n' % os.path.join(HTTPLINK,REPDIR,y))
            break
    # insert link to detail log, if available
    for y in ldir:
        if y.find(fdate) > -1:
            dayhtmlf.write('<p>See detailed log: <a href="%s">%s</a></p>\n' % 
                (os.path.join(HTTPLINK,FINDIR,y), y))
            break
    # write prev, up, next links
    write_prev_up_next(dayhtmlf, idate, to_process)
    # write trailer html
    for line in trailerf:
        dayhtmlf.write(line)
    trailerf.close()
    dayhtmlf.close()
    # Add link entry to index file
    thisLink = os.path.join(HTTPLINK, dayhtmlfn)    # HTTP link to this new file
    ixf.write('<a href="%s">%s</a><br />\n' % (thisLink, fdate_expanded))
        
# Finish the index file
ixtrf = open(IXTRAILER,'r')
for line in ixtrf:
    ixf.write(line)
ixtrf.close()
ixf.close()
