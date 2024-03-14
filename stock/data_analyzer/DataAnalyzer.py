import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from ..data_acquisitor import DataAcquisitor


class DataAnalyzer(object):
	'''
	Information extractor and analyzer based on the stock data
	'''

	# class-level (static) members
	IGNORE           = -3
	EMPTY            = -2
	SELL             = -1
	SPECULATE        = 0
	SELL_OR_HESITATE = 1
	RISING_SHORT     = 2
	RISING_LONG      = 3
	PeriodAlias = [[0, "d", "D", "Day", "day"],
				   [1, "w", "W",  "Week", "week"],
				   [2, "m", "M", "Month", "month"],
				   [3, "h", "H", "Hour", "hour"]]

	def __init__(self, dataAcquired: DataAcquisitor):
		'''
		param:
			dataAcquired: DataAcquisitor containing the stock data
		'''
		self._dataAcquired = dataAcquired
		self._MADay   = {5: self.compute_moving_average(0, 5),
					    10: self.compute_moving_average(0, 10),
					    20: self.compute_moving_average(0, 20),
					    60: self.compute_moving_average(0, 60)}
		self._MAWeek  = {5: self.compute_moving_average(1, 5),
					    10: self.compute_moving_average(1, 10),
					    20: self.compute_moving_average(1, 20),
					    60: self.compute_moving_average(1, 60)}
		self._MAMonth = {5: self.compute_moving_average(2, 5),
					    10: self.compute_moving_average(2, 10),
					    20: self.compute_moving_average(2, 20)}
		self._MAHour =  {5: self.compute_moving_average(3, 5),
					    20: self.compute_moving_average(3, 20),
					    60: self.compute_moving_average(3, 60)}
#		self._smoothedDayMA5   = self.compute_smoothed_MA5(0, 11, deriv = 0)
#		self._smoothedWeekMA5  = self.compute_smoothed_MA5(1, 11, deriv = 0)
#		self._smoothedMonthMA5 = self.compute_smoothed_MA5(2, 11, deriv = 0)
#		self._smoothedHourMA5  = self.compute_smoothed_MA5(3, 11, deriv = 0)
        # smoothed derivatives is used to find local extrema
#		self._smoothedDerivativeDayMA5   = self.compute_smoothed_MA5(0, 11, deriv = 1)
#		self._smoothedDerivativeWeekMA5  = self.compute_smoothed_MA5(1, 11, deriv = 1)
#		self._smoothedDerivativeMonthMA5 = self.compute_smoothed_MA5(2, 11, deriv = 1)
#		self._smoothedDerivativeHourMA5  = self.compute_smoothed_MA5(3, 11, deriv = 1)
#		self._lastMaximumDayMA5   = self.compute_historical_maximum_closest_to_today(0)
#		self._lastMaximumWeekMA5  = self.compute_historical_maximum_closest_to_today(1)
#		self._lastMaximumMonthMA5 = self.compute_historical_maximum_closest_to_today(2)
#		self._lastMaximumHourMA5  = self.compute_historical_maximum_closest_to_today(3)
        # simply approximate derivatives f today's trends by finite difference of MAs
		self._derivativeTodayDay   = {5: self.compute_derivative_today(0, 5, stencil = 1),
									 20: self.compute_derivative_today(0, 20, stencil = 1),
									 60: self.compute_derivative_today(0, 60, stencil = 1)}
		self._derivativeTodayWeek  = {5: self.compute_derivative_today(1, 5, stencil = 1),
									 20: self.compute_derivative_today(1, 20, stencil = 1),
									 60: self.compute_derivative_today(1, 60, stencil = 1)}
		self._derivativeTodayMonth = {20: self.compute_derivative_today(2, 20, stencil = 1)}
		self._derivativeTodayHour  = {5: self.compute_derivative_today(3, 5, stencil = 2),
									 20: self.compute_derivative_today(3, 20, stencil = 2),
									 60: self.compute_derivative_today(3, 60, stencil = 1)}

	def get_data_acquired(self) -> DataAcquisitor :
		'''
		return DataAcquisitor that contains the stock trading data
		'''
		return self._dataAcquired

	def get_closing_price_history(self, period) -> pd.DataFrame:
		'''
		param:
			period: day - 0, week - 1, month - 2, hour - 3
		'''
		if period in self.PeriodAlias[0]:
			return self._dataAcquired.get_day_k()["Close"]
		elif period in self.PeriodAlias[1]:
			return self._dataAcquired.get_week_k()["Close"]
		elif period in self.PeriodAlias[2]:
			return self._dataAcquired.get_month_k()["Close"]
		else:
			return self._dataAcquired.get_hour_k()["Close"]

	def get_closing_price_today(self):
		price = self.get_closing_price_history(0)
		return price[price.shape[0] - 1]

	def compute_moving_average(self, period, window: int) -> np.ndarray: # for now I just assume we have enough data, otherwise simply skip
		'''
		param:
			period: day - 0, week - 1, month - 2, hour - 3
		'''
		data = self.get_closing_price_history(period)

		if len(data) < window: # not enough data, should only happen to Month-K
			return np.zeros(1)

		try:
			movingAverages = np.convolve(data, np.ones(window) / window, mode = "valid")
			return movingAverages.round(decimals = 2)
		except:
			return np.zeros(1)

	def get_moving_average(self, period) -> np.ndarray:
		'''
		param:
			period: day - 0, week - 1, month - 2, hour - 3
		'''
		if period in self.PeriodAlias[0]:
			return self._MADay
		elif period in self.PeriodAlias[1]:
			return self._MAWeek
		elif period in self.PeriodAlias[2]:
			return self._MAMonth
		else:
			return self._MAHour


	def compute_smoothed_MA5(self, period, window: int, deriv: int = 0, **kwargs) -> np.ndarray:
		'''
		smooth data using a cubic Savitzky–Golay filter

		param:
			period: day - 0, week - 1, month - 2, hour - 3
			window: size of the window
			deriv: n-th derivative
		'''
		data = self.get_moving_average(period)[5]
		return savgol_filter(data, window, 3, deriv, **kwargs)

	def compute_derivative_today(self, period, window: int, stencil: int = 2) -> np.float64:
		'''
		param:
			period: day - 0, week - 1, month - 2, hour - 3
		'''
		MA = self.get_moving_average(period)[window]
		try:
			return np.round((MA[-1] - MA[-1 - stencil]) / stencil, 3)
		except:
			return 0.0

	def get_derivative_today(self, period):
		if period in self.PeriodAlias[0]:
			return self._derivativeTodayDay
		elif period in self.PeriodAlias[1]:
			return self._derivativeTodayWeek
		elif period in self.PeriodAlias[2]:
			return self._derivativeTodayMonth
		else:
			return self._derivativeTodayHour

	def compute_historical_maximum_closest_to_today(self, period) -> np.float64:
		'''
		param:
			period: day - 0, week - 1 or month - 2
		'''
		if period in self.PeriodAlias[0]:
			MA5, dMA5 = self._smoothedDayMA5, self._smoothedDerivativeDayMA5
		elif period in self.PeriodAlias[1]:
			MA5, dMA5 = self._smoothedWeekMA5, self._smoothedDerivativeWeekMA5
		elif period in self.PeriodAlias[2]:
			MA5, dMA5 = self._smoothedMonthMA5, self._smoothedDerivativeMonthMA5
		else:
			MA5, dMA5 = self._smoothedHourMA5, self._smoothedDerivativeHourMA5

		for i in range(len(MA5) - 2, -1, -1):
			if dMA5[i] > 0 and dMA5[i + 1] < 0: # I don't think I need to bother with dMA5 == 0 but I will make it robuster later
				return MA5[i]
		return 10000

	def get_historical_maximum_closest_to_today(self, period) -> np.float64:
		if period in self.PeriodAlias[0]:
			return self._lastMaximumDayMA5
		elif period in self.PeriodAlias[1]:
			return self._lastMaximumWeekMA5
		elif period in self.PeriodAlias[2]:
			return self._lastMaximumMonthMA5
		else:
			return self._lastMaximumHourMA5

	def _check_MA_trend(self, length: str) -> int:
		if length == "short":
			MA = self.get_moving_average("Hour")
			dMA = self.get_derivative_today("Hour")
		else:
			MA = self.get_moving_average("Day")
			dMA = self.get_derivative_today("Day")

		# falling trend
		if MA[5][-1] < MA[60][-1]:
			if dMA[5] < 0:
				if dMA[60] < 0:
					return self.EMPTY
				return self.SELL
#			return self.SPECULATE # check this criteria!!! Usually in order to make a rising trend, MAs of the shortest period should follow MA5 >= MA60
		# downturn of trend
		if MA[5][-1] < MA[20][-1]:
			if dMA[20] < 0:
				return self.SELL
		if length == "long" and self.get_closing_price_today() < MA[20][-1]:
			if self._check_MA_trend("short") <= 0:
				return self.SELL_OR_HESITATE
		# rising trend
		return self.RISING_SHORT if length == "short" else self.RISING_LONG

	def send_signal(self, priceLimit) -> int:
		priceClosing = self.get_closing_price_today()
		if (priceClosing > priceLimit): # at most 100 * priceLimit RMB to buy in
			return int(-priceLimit)

		### short term
		if self._derivativeTodayDay[20] >= 0 and self._derivativeTodayWeek[20] >= 0 and self._derivativeTodayMonth[20] < 0:
			return self._check_MA_trend("short")
		### long term
		elif (self._derivativeTodayWeek[20] >= 0 and self._derivativeTodayMonth[20] >= 0):
			# potential "terminal lucidity"
			# if(priceClosing < 0.98 * min(self._lastMaximumWeekMA5, self._lastMaximumMonthMA5)):
				# if priceClosing >= 0.94 * self._lastMaximumDayMA5:
					# return self.RISING_SHORT
				# return self.SPECULATE
			return self._check_MA_trend("long")
		# Noob, let's start with simple trends
		elif (self._derivativeTodayDay[20] < 0 and self._derivativeTodayWeek[20] < 0):
			return self.IGNORE
		else:
			return self.SPECULATE

	def plot_MA_and_K(self, period,ax = None):
		MA = self.get_moving_average(period)
		if period in self.PeriodAlias[0]:
			kHistory = self._dataAcquired.get_day_k()
			period = " Day"
		elif period in self.PeriodAlias[1]:
			kHistory = self._dataAcquired.get_week_k()
			period = " Week"
		elif period in self.PeriodAlias[2]:
			kHistory = self._dataAcquired.get_month_k()
			period = " Month"
		else:
			kHistory = self._dataAcquired.get_hour_k()
			period = " Hour"

		windows = list(MA.keys())
		mycolor=mpf.make_marketcolors(up="red",down="green",edge="i",wick="i",volume="in")
		mystyle=mpf.make_mpf_style(marketcolors=mycolor,gridaxis="both",gridstyle="-.")
		fig, axes = mpf.plot(kHistory, type = 'candle', mav = windows,
							 volume = True, show_nontrading = False,
							 style = mystyle,
							 warn_too_much_data = 5215,
							 returnfig = True)
		axes[0].set_title(self._dataAcquired.get_code() + period,
						  fontsize=16, style='normal', fontfamily='Helvetica',
						  loc='center')
		plt.show()
		plt.close()
