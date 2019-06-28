#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-
# this code indented with actual 0x09 tabs

import os sys math
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def proof_dir(dir_path):
	try:
		os.stat(dir_path)
	except:
		os.makedirs(dir_path)

def proof_dat_f(dat_f_path):
	try:
		os.stat(dat_f_path)
	except:
		open(dat_f_path, 'a').close()

def write_out(file_name, data, mode):
	out_file_fd = open(file_name, mode)
	out_file_fd.write(data)
	out_file_fd.close()

def write_out_dat_stamp(ts, n_plate, data, wx_dir):
	f_ts = ts[0:8]
	y_ts = ts[0:4]
	out_dir = wx_dir+'/data/'+y_ts
	proof_dir(out_dir)
	write_out(out_dir+'/'+n_plate+'.'+f_ts, data, 'a')

# based on:
# https://en.wikipedia.org/wiki/Vapour_pressure_of_water
# https://en.wikipedia.org/wiki/Arden_Buck_equation
def buck_eq_kPa(temp_c):
	if (temp_c >= 0):
		c1 = 0.61121
		c2 = 18.678
		c3 = 234.84
		c4 = 257.14

	if (temp_c < 0):
		c1 = 0.61115
		c2 = 23.036
		c3 = 333.7
		c4 = 279.82

	# saturation vapor pressure of water
	Psv = c1 * math.exp((c2 - temp_c / c3) * (temp_c / (c4 + temp_c)))

	return Psv

def graph(lx, ly, lfmt, ltitle, lylabel, lfname):
	# default font can't do subscript ₂
	mpl.rc('font', family='DejaVu Sans')

	plt.figure(figsize=(20, 6), dpi=100)
	plt.grid(True)
	plt.plot_date(x = lx, y = ly, fmt = lfmt)
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M:%S'))
	plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=4))
	plt.minorticks_on()
	plt.gcf().autofmt_xdate()
	plt.title(ltitle)
	plt.xlabel("Date (UTC)")
	plt.ylabel(lylabel)
	ymin, ymax = plt.ylim()
	plt.twinx()
	plt.minorticks_on()
	plt.ylim(ymin, ymax)
	plt.ylabel(lylabel)
	plt.tight_layout()
	plt.savefig(lfname)
	plt.close()
