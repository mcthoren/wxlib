#!/usr/local/bin/python2.7
# -*- coding: UTF-8 -*-
# this code indented with actual 0x09 tabs

import os, sys, math

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

# dew point equations and constants from:
# http://journals.ametsoc.org/doi/pdf/10.1175/BAMS-86-2-22
def dew_point_c(temp_c, rh):
	Ca = 17.625
	Cb = 243.04 # [°C]

        gamma = math.log(rh / 100) + ((Ca * temp_c) / (Cb + temp_c))
        Tdew = (Cb * gamma) / (Ca - gamma)

	return Tdew

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

# based on:
# https://en.wikipedia.org/wiki/Humidity
# https://en.wikipedia.org/wiki/Ideal_gas_law
# https://en.wikipedia.org/wiki/Gas_constant
def abs_hum_g_mmm(temp_c, rh):
	# P V = m Rs T		# ideal gas law
	# → Pp V = m Rs T	# where pressure here is partial pressure for water
	# → V / m = Rs T / Pp
	# ∴ m / V = Pp / Rs T	# mass / vol is abs hum
	#
	# RH = 100 * Pp/Ps	# Ps : saturation vapor pressure (water)
	# → Pp = RH * Ps / 100

	Ps = buck_eq_kPa(temp_c) * 1000 # 1000 Pa / kPa
	Pp = rh * Ps / 100

	# Rs = R/MH₂O = 8.314462618 [m³⋅Pa/K⋅mol] / 18.01528 [g/mol]
	Rs = 0.4615228 # [m³·Pa / K·g]

	# [m / V] = [Pa] / ( [m³·Pa / K·g] · [K] ) = [Pa·K·g / m³·Pa·K]  = [g / m³]
	m_V = Pp / (Rs * (temp_c + 273.15))

	return m_V # [g / m³]

# based on https://en.wikipedia.org/wiki/Heat_index
def heat_index(temp_c, rh):
	if (temp_c < 27 or temp_c > 44):
		return -1

	if (rh < 40 or rh > 100):
		return -1

	c1 = -8.78469475556
	c2 = 1.61139411
	c3 = 2.33854883889
	c4 = -0.14611605
	c5 = -0.012308094
	c6 = -0.0164248277778
	c7 = 0.002211732
	c8 = 0.00072546
	c9 = -0.000003582

	# with enough parameters, you can fit a curve to a cow
	hi = c1 + c2 * temp_c + c3 * rh + c4 * temp_c * rh + c5 * temp_c * temp_c + \
	c6 * rh * rh + c7 * temp_c * temp_c * rh + \
	c8 * temp_c * rh * rh + c9 * temp_c * temp_c * rh * rh

	return hi

# should grab temp of most raspberry pis
def pi_temp_read():
	temp_file = "/sys/class/thermal/thermal_zone0/temp"
	temp_file_fd = open(temp_file, 'r')

	temp_data = temp_file_fd.read()
	temp_file_fd.close()

	return temp_data

def bmp085_read():
	# https://www.adafruit.com/products/391
	# https://github.com/adafruit/Adafruit_Python_BMP/
	import Adafruit_BMP.BMP085 as BMP085

	pressures = []
	iter = 16
	avg = 0

	sensor = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES, busnum=0)

	temp = sensor.read_temperature()

	# datasheet suggests averaging
	for x in range(0, iter):
		pressures.append(sensor.read_pressure())
		avg += pressures[x]

	avg = avg / iter

	return (temp, avg / 1000.0)

def sht11_read():
	# roughly the reference implementation:
	# https://pypi.python.org/pypi/rpiSht1x/1.2

	from sht1x.Sht1x import Sht1x as SHT1x
	dataPin = 16
	clkPin = 7

	sht1x = SHT1x(dataPin, clkPin, SHT1x.GPIO_BOARD)

	temp = sht1x.read_temperature_C()
	hum = sht1x.read_humidity()
	T_dew = sht1x.calculate_dew_point(temperature, humidity)

	return (temp, hum, T_dew)

def htu21df_read():
	# https://www.adafruit.com/product/1899
	# https://github.com/adafruit/Adafruit_HTU21DF_Library/
	# https://github.com/dalexgray/RaspberryPI_HTU21DF/

	import Adafruit_GPIO.I2C as I2C

	temp_read = 0xE3
	hum_read = 0xE5
	write_reg = 0xE6
	soft_reset = 0xFE

	htu_addy = 0x40
	bus = 0

	array = [0x00, 0x00]

	dev0 = I2C.Device(htu_addy, bus)
	dev0.write8(soft_reset, write_reg) # does this actually reset it? prly not....
	time.sleep(0.2)

	array = dev0.readList(temp_read, 2)
	t0 = (array[0] * 256.0) + array[1]
	temp = ((t0 * 175.72) / 65536) - 46.85

	array = dev0.readList(hum_read, 2)
	h0 = (array[0] * 256.0) + array[1]
	hum = ((h0 * 125) / 65536) - 6

	return (temp, hum)

def bme680_read():
	# sensor + breakout board from:
	# https://www.adafruit.com/product/3660

	# libraries and examples from:
	# https://learn.pimoroni.com/tutorial/sandyj/getting-started-with-bme680-breakout

	import bme680, time

	iter = 16
	avg = 0

	sensor = bme680.BME680(i2c_addr=0x77)

	sensor.set_humidity_oversample(bme680.OS_2X)
	sensor.set_pressure_oversample(bme680.OS_4X)
	sensor.set_temperature_oversample(bme680.OS_8X)
	# sensor.set_filter(bme680.FILTER_SIZE_3)
	sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

	sensor.set_gas_heater_temperature(320)
	sensor.set_gas_heater_duration(150)
	sensor.select_gas_heater_profile(0)

	temp = sensor.data.temperature
	hum = sensor.data.humidity

	# go back to averaging pressure samples as in the bmp085 datasheet
	for x in range(0, iter):
		avg += sensor.data.pressure

	pres_avg = avg / iter # [hPa]

	gas_res = 0
	tries = 5

	while (tries > 0):
		sensor.get_sensor_data()
		if sensor.data.heat_stable:
			gas_res = sensor.data.gas_resistance
		else:
			time.sleep(1)

		tries = tries - 1

	return (temp, hum, pres_avg / 10, gas_res)

def graph(lx, ly, lfmt, ltitle, lylabel, lfname):
	import matplotlib as mpl
	mpl.use('Agg')
	import matplotlib.pyplot as plt
	import matplotlib.dates as mdates

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
