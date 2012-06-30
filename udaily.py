#!/usr/bin/env python

# File: udaily.py
# Version: 0.1
# Date: 7 Oct 2008
# Author: Martin S. Ewing

#    udaily.py runs daily to generate reports and graphs from log files.
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

import os,os.path,sys

PENDIR = "logs/pending"		# Where to find log files
FINDIR = "logs/processed"	# Where the logs will finish up
REPDIR = "reports"		# Where to put reports and plots

# when udaily.py is run, check for any files in PENDIR, generate reports
# & plots in REPDIR, then move the file to FINDIR.

# To Do:
# Enhance report (sum times, range of temps, means, ...)
# Produce HTML
# Provide for CLI rerun of reports
# automate reports @ wee hours
# archive data - > tgz?

def print2(s,id):		# print sting to both stdout & id
	print >>id, s
	print s

def report(date):		# report from log of given date
	ifn = PENDIR+"/ulog"+date+".log"
	ifd = open(ifn, 'r')	# open input log
	rfn = REPDIR+"/rept"+date+".txt"
	rfd = open(rfn, 'w')	# and report output
	pfn = REPDIR+"/plcm"+date+".dat"
	pfd = open(pfn, 'w')	# plot file name (gnuplot cmd input)
	nsamples= nfurn= nhw= nz1= nz2= nz3 = 0	# accumulated time samples
	thw_min=tamb_min = 99.
	thw_max=tamb_max = -99.
	tamb_sum = 0.
	for line in ifd:	# Scan file to make print report
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
			continue	# Don't count a bad line
		nsamples += 1
		thw_min = min(thw_min,thw)
		thw_max = max(thw_max,thw)
		tamb_min = min(tamb_min,tamb)
		tamb_max = max(tamb_max,tamb)
		tamb_sum += tamb
		if fhw : 	nhw += 1
		if ffurn : 	nfurn += 1
		if fz1 :	nz1 += 1
		if fz2 :	nz2 += 1
		if fz3 :        nz3 += 1
	print2("Daily report for %s" % date, rfd)
	durmin = 0.5*nsamples	# presumed minutes spanned
	durhr = durmin/60.0
	print2("\n%.1f minutes = %.2f hours recorded." % (durmin, durhr), rfd)
	print2("Ambient temp = %.2f (max), %.2f (min), %.2f (avg)" % 
		(tamb_max, tamb_min, tamb_sum / float(nsamples)), rfd)
	print2("On times (min): %.1f (furnace),"
		" %.1f (HW), %.1f (Z1), %.1f (Z2), %.1f (Z3)" % 
		(nfurn/2., nhw/2., nz1/2., nz2/2., nz3/2.), rfd)
	cost = nfurn*1.50*2.87/120.
	print2("@ 1.50 gallons/hr, $2.87/gallon, cost = $%.2f" %
		cost, rfd)
	rfd.close()
	ifd.close()

	# Make gnuplot initial command file specifying input file & output png	
	print >>pfd, 'file="%s"' % ifn
	print >>pfd, 'set output "%s/plot%s.png"' % (REPDIR, date)
	pfd.close()
	# Launch gnuplot
	gnucmd = "gnuplot %s gnuplot.prog" % pfn
	success = os.system(gnucmd)
	if success <> 0:
		print "*** gnuplot has failed."
	os.remove(pfn)

# scan for ulogYYYYMMDD.log files in PENDIR.  If present, do the reports.

log_list = os.listdir(PENDIR)
for x in log_list:
	if x[-1] is "~":	# ignore any backups from vi, etc.
		continue
	date_part = x[4:12]	# YYYYMMDD
	report(date_part)	# do the interesting stuff
	# Move file to FINDIR
	os.rename(os.path.join(PENDIR,x),os.path.join(FINDIR,x))
