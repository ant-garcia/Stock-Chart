import sys
import time
import pylab
import urllib2
import datetime
import matplotlib

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import matplotlib.animation as animation

from matplotlib.finance import candlestick_ohlc

fig = plt.figure(facecolor = '#07000d')
matplotlib.rcParams.update({'font.size' : 9})

def calc_rsi(prices):
	n = 14
	deltas = np.diff(prices)
	seed = deltas[:n + 1]
	up = seed[seed >= 0].sum() / n
	down = -seed[seed < 0].sum() / n
	rs = up / down
	rsi = np.zeros_like(prices)
	rsi[:n] = 100. - 100. / (1. + rs)

	for i in range(n, len(prices)):
		delta = deltas[i - 1]
		if delta > 0:
			upval = delta
			downval = 0.

		else:
			upval = 0.
			downval = -delta

		up = (up * ( n - 1) + upval) / n
		down = (down * ( n - 1) + downval) / n
		rs = up / down
		rsi[i] = 100. - 100. / (1. + rs)
	return rsi

def moving_avg(values, window):
	weights = np.repeat(1.0, window) / window
	smas = np.convolve(values, weights, 'valid')
	return smas

def exp_moving_avg(values, window):
	weights = np.exp(np.linspace(-1., 0., window))
	weights /= weights.sum()
	a = np.convolve(values, weights, mode = 'full')[:len(values)]
	a[:window] = a[window]
	return a

def calc_MACD(x):
	slow = 26
	fast = 12
	ema_slow = exp_moving_avg(x, slow)
	ema_fast = exp_moving_avg(x, fast)
	return ema_slow, ema_fast, ema_fast - ema_slow

def pull_stock_data(stock):
	try:
		print 'Currently Pulling', stock
		print str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
		url_to_visit = 'http://chartapi.finance.yahoo.com/instrument/1.0/'+stock+'/chartdata;type=quote;range=1d/csv'
		stock_data = []
		try:
			stock_src = urllib2.urlopen(url_to_visit).read()
			split_source = stock_src.split('\n')

			for line in split_source:
				split_line = line.split(',')
				format_date = split_line[0]
				if len(split_line) == 6:
					if 'values' not in line:
						formatted_line = line.replace(format_date,
							str(datetime.datetime.fromtimestamp(int(format_date)).strftime('%Y-%m-%d %H:%M:%S')))
						stock_data.append(formatted_line)
		except Exception, e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			print "Error at line %d: %s" % (exc_tb.tb_lineno, str(e))

	except Exception, e:
		exc_type, exc_obj, exc_tb = sys.exc_info()
		print "Error at line %d: %s" % (exc_tb.tb_lineno, str(e))

	return stock_data

def generate_price_plot(date, closep, highp, lowp, openp, volume, MA1, MA2, starting_point,
						use_candle, show_average):
	x = 0
	y = len(date)
	candleAr = []
	while x < y:
		appendLine = date[x], openp[x], highp[x], lowp[x], closep[x], volume[x]
		candleAr.append(appendLine)
		x += 1

	price_plot = plt.subplot2grid((6, 4), (1, 0), rowspan = 4, colspan = 4, axisbg = '#07000d')

	if use_candle == True:
		candlestick_ohlc(price_plot, candleAr[-starting_point:], width = .0005, colorup = '#9eff15', colordown = '#ff1717')
	else:
		price_plot.plot(date[-starting_point:], highp[-starting_point:], color = '#5998ff',
						label = '_nolegend_')
	if show_average == True:
		av1 = moving_avg(closep, MA1)
		av2 = moving_avg(closep, MA2)
		label1 = str(MA1) + ' SMA'
		label2 = str(MA2) + ' SMA'
		price_plot.plot(date[-starting_point:], av1[-starting_point:], '#5998ff', label = label1, 
						linewidth = 1.5)
		price_plot.plot(date[-starting_point:], av2[-starting_point:], '#e1edf9', label = label2, 
						linewidth = 1.5)
		legend = plt.legend(loc = 9, ncol = 2, prop = {'size' : 7},
					    fancybox = True, borderaxespad = 0.)
		legend.get_frame().set_alpha(0.4)
		textEd = pylab.gca().get_legend().get_texts()
		pylab.setp(textEd[0:5], color = 'w')
	
	price_plot.grid(True, color = 'w')
	price_plot.xaxis.set_major_locator(mticker.MaxNLocator(10))
	plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune = 'upper'))
	price_plot.yaxis.label.set_color('w')
	price_plot.spines['bottom'].set_color('#5998ff')
	price_plot.spines['top'].set_color('#5998ff')
	price_plot.spines['left'].set_color('#5998ff')
	price_plot.spines['right'].set_color('#5998ff')
	price_plot.tick_params(axis = 'y', colors = 'w')
	price_plot.tick_params(axis = 'x', colors = 'w')
	plt.ylabel('Stock Price and Volume')
	
	volume_plot = price_plot.twinx()
	volume_plot.fill_between(date[-starting_point:], 0, volume[-starting_point:],
							 facecolor = '#00ffe8', alpha = .4)
	volume_plot.axes.yaxis.set_ticklabels([])
	volume_plot.grid(False)
	volume_plot.spines['bottom'].set_color('#5998ff')
	volume_plot.spines['top'].set_color('#5998ff')
	volume_plot.spines['left'].set_color('#5998ff')
	volume_plot.spines['right'].set_color('#5998ff')
	volume_plot.set_ylim(0, 3 * volume.max())
	volume_plot.tick_params(axis = 'x', colors = 'w')
	volume_plot.tick_params(axis = 'y', colors = 'w')
	plt.setp(price_plot.get_xticklabels(), visible = False)

def generate_rsi_plot(date, closep, starting_point):
	rsi = calc_rsi(closep)
	rsi_color = '#00ffe8'
	pos_color = '#9eff15'
	neg_color = '#ff1717'
	rsi_plot = plt.subplot2grid((6, 4), (0, 0), sharex = plt.gca(), rowspan = 1, colspan = 4, axisbg = '#07000d')
	rsi_plot.plot(date[-starting_point:], rsi[-starting_point:], rsi_color, linewidth = 1.5)
	rsi_plot.axhline(70, color = neg_color)
	rsi_plot.axhline(30, color = pos_color)
	rsi_plot.fill_between(date[-starting_point:], rsi[-starting_point:], 70,
						  where = (rsi[-starting_point:] >= 70), facecolor = neg_color,
						  edgecolor = neg_color)
	rsi_plot.fill_between(date[-starting_point:], rsi[-starting_point:], 30,
						  where = (rsi[-starting_point:] <= 30), facecolor = pos_color,
					      edgecolor = pos_color)
	rsi_plot.spines['bottom'].set_color('#5998ff')
	rsi_plot.spines['top'].set_color('#5998ff')
	rsi_plot.spines['left'].set_color('#5998ff')
	rsi_plot.spines['right'].set_color('#5998ff')
	rsi_plot.tick_params(axis = 'x', colors = 'w')
	rsi_plot.tick_params(axis = 'y', colors = 'w')
	rsi_plot.set_yticks([30, 70])
	rsi_plot.yaxis.label.set_color('w')
	plt.setp(rsi_plot.get_xticklabels(), visible = False)
	plt.ylabel('RSI')


def generate_macd_plot(date, closep, starting_point):
	macd_plot = plt.subplot2grid((6, 4), (5, 0), sharex = plt.gca(), rowspan = 1, colspan = 4,
					        	 axisbg = '#07000d')
	fill_color = '#00ffe8'
	nema = 9
	ema_slow, ema_fast, macd = calc_MACD(closep)
	ema9 = exp_moving_avg(macd, nema)

	macd_plot.plot(date[-starting_point:], macd[-starting_point:], color = '#4ee6fd')
	macd_plot.plot(date[-starting_point:], ema9[-starting_point:], color = '#e1edf9')
	macd_plot.fill_between(date[-starting_point:], macd[-starting_point:] - ema9[-starting_point:],
	 					   0, alpha = .5, facecolor = fill_color, edgecolor = fill_color)
	plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune = 'upper'))
	macd_plot.spines['bottom'].set_color('#5998ff')
	macd_plot.spines['top'].set_color('#5998ff')
	macd_plot.spines['left'].set_color('#5998ff')
	macd_plot.spines['right'].set_color('#5998ff')
	macd_plot.tick_params(axis = 'x', colors = 'w')
	macd_plot.tick_params(axis = 'y', colors = 'w')
	macd_plot.yaxis.set_major_locator(mticker.MaxNLocator(nbins = 5, prune = 'upper'))
	plt.ylabel('MACD', color = 'w')

def graph_data(stock, MA1, MA2):
	fig.clf()
	stock_data = pull_stock_data(stock)
	date, closep, highp, lowp, openp, volume = np.loadtxt(stock_data, delimiter = ',',
														   unpack = True,
														   converters = {0: mdates.strpdate2num('%Y-%m-%d %H:%M:%S')})
	starting_point = len(date[MA2 - 1:])

	generate_price_plot(date, closep, highp, lowp, openp, volume, MA1, MA2, starting_point,
						True, False)
	generate_rsi_plot(date, closep, starting_point)
	generate_macd_plot(date, closep, starting_point)

	
	plt.suptitle(stock, color = 'w')
	plt.gca().xaxis.set_major_locator(mticker.MaxNLocator(10))
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
	plt.setp(plt.gca().get_xticklabels(), rotation = 90)
	plt.subplots_adjust(left = .09, bottom = .18, top = .94, right = .95, wspace = .20,
						hspace = 0)

def animate(i):
	graph_data(stock, 10, 50)

while True:
	stock = raw_input('Stock to chart: ')
	ani = animation.FuncAnimation(fig, animate, interval = 5000)
	plt.show()	