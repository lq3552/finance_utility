import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import pandas as pd
from DataAcquisitor import DataAcquisitor


class DataAnalyzer(object):
	'''
	Information extractor and analyzer based on the stock data
	'''

	# class-level (static) members
	EMPTY        = -2
	SELL         = -1
	WAIT         = 0
	RISING_SHORT = 1
	RISING_LONG  = 2
	PeriodAlias = [[0, "d", "Day", "day"],
				   [1, "w", "Week", "week"],
				   [2, "m", "Month", "month"]]

	def __init__(self, dataAcquired: DataAcquisitor):
		'''
		param:
			dataAcquired: DataAcquisitor containing the stock data
		'''
		self._dataAcquired = dataAcquired
		self._MADay   = {5:    self.compute_moving_average(0, 5),
					    10:   self.compute_moving_average(0, 10),
					    20:   self.compute_moving_average(0, 20),
					    60:   self.compute_moving_average(0, 60)}
		self._MAWeek  = {5:   self.compute_moving_average(1, 5),
					    10:  self.compute_moving_average(1, 10),
					    20:  self.compute_moving_average(1, 20),
					    60:  self.compute_moving_average(1, 60)}
		self._MAMonth = {5:  self.compute_moving_average(2, 5),
					    10: self.compute_moving_average(2, 10),
					    20: self.compute_moving_average(2, 20)}
		self._smoothedDayMA5   = self.compute_smoothed_MA5(0, 11, deriv = 0)
		self._smoothedWeekMA5  = self.compute_smoothed_MA5(1, 11, deriv = 0)
		self._smoothedMonthMA5 = self.compute_smoothed_MA5(2, 11, deriv = 0)
        # smoothed derivatives is used to find local extrema
		self._smoothedDerivativeDayMA5   = self.compute_smoothed_MA5(0, 11, deriv = 1)
		self._smoothedDerivativeWeekMA5  = self.compute_smoothed_MA5(1, 11, deriv = 1)
		self._smoothedDerivativeMonthMA5 = self.compute_smoothed_MA5(2, 11, deriv = 1)
		self._lastMaximumDayMA5   = self.compute_historical_maximum_closest_to_today(0)
		self._lastMaximumWeekMA5  = self.compute_historical_maximum_closest_to_today(1)
		self._lastMaximumMonthMA5 = self.compute_historical_maximum_closest_to_today(2)
        # simply approximate derivatives f today's trends by finite difference of MAs
		self._derivativeTodayDay   = {5:  self.compute_derivative_today(0, 5),
									 20: self.compute_derivative_today(0, 20),
									 60: self.compute_derivative_today(0, 60)}
		self._derivativeTodayWeek  = {5:  self.compute_derivative_today(1, 5),
									 20: self.compute_derivative_today(1, 20),
									 60: self.compute_derivative_today(1, 60)}
		self._derivativeTodayMonth = {20: self.compute_derivative_today(2, 20)}

	def get_data_acquired(self) -> DataAcquisitor :
		'''
		return DataAcquisitor that contains the stock trading data
		'''
		return self._dataAcquired

	def get_closing_price_history(self, period) -> pd.DataFrame:
		'''
		param:
			period: day - 0, week - 1 or month - 2
		'''
		if period in self.PeriodAlias[0]:
			return self._dataAcquired.get_day_k()["收盘"]
		elif period in self.PeriodAlias[1]:
			return self._dataAcquired.get_week_k()["收盘"]
		else:
			return self._dataAcquired.get_month_k()["收盘"]

	def get_moving_average(self, period) -> np.ndarray:
		'''
		param:
			period: day - 0, week - 1 or month - 2
		'''
		if period in self.PeriodAlias[0]:
			return self._MADay
		elif period in self.PeriodAlias[1]:
			return self._MAWeek
		else:
			return self._MAMonth

	def compute_moving_average(self, period, window: int) -> np.ndarray: # for now I just assume we have enough data, otherwise simply skip
		'''
		param:
			period: day - 0, week - 1 or month - 2
		'''
		data = self.get_closing_price_history(period)

		if len(data) < window: # not enough data, should only happen to Month-K
			return np.zeros(1)

		try:
			movingAverages = np.convolve(data, np.ones(window) / window, mode = "valid")
			return movingAverages
		except:
			return np.zeros(1)

	def compute_smoothed_MA5(self, period, window: int, deriv: int = 0, **kwargs) -> np.ndarray:
		'''
		smooth data using a cubic Savitzky–Golay filter

		param:
			period: day - 0, week - 1 or month - 2
			window: size of the window
		'''
		data = self.get_moving_average(period)[5]
		return savgol_filter(data, window, 3, deriv, **kwargs)

	def get_derivative_today(self, period):
		if period in self.PeriodAlias[0]:
			return self._derivativeTodayDay
		elif period in self.PeriodAlias[1]:
			return self._derivativeTodayWeek
		else:
			return self._derivativeTodayMonth
		return

	def compute_derivative_today(self, period, window: int, stencil: int = 2) -> np.float64:
		'''
		param:
			period: day - 0, week - 1 or month - 2
		'''
		MA = self.get_moving_average(period)[window]
		try:
			return (MA[-1] - MA[-1 - stencil]) / stencil
		except:
			return 0.0

	def get_historical_maximum_closest_to_today(self, period) -> np.float32:
		if period in self.PeriodAlias[0]:
			return self._lastMaximumDayMA5
		elif period in self.PeriodAlias[1]:
			return self._lastMaximumWeekMA5
		else:
			return self._lastMaximumMonthMA5
		return

	def compute_historical_maximum_closest_to_today(self, period) -> np.float32:
		'''
		param:
			period: day - 0, week - 1 or month - 2
		'''
		if period in self.PeriodAlias[0]:
			MA5, dMA5 = self._smoothedDayMA5, self._smoothedDerivativeDayMA5
		elif period in self.PeriodAlias[1]:
			MA5, dMA5 = self._smoothedWeekMA5, self._smoothedDerivativeWeekMA5
		else:
			MA5, dMA5 = self._smoothedMonthMA5, self._smoothedDerivativeMonthMA5

		for i in range(len(MA5) - 2, -1, -1):
			if dMA5[i] > 0 and dMA5[i + 1] < 0: # I don't think I need to bother with dMA5 == 0 but I will make it robuster later
				return MA5[i]
		return 10000

	def get_closing_price_today(self):
		price = self._dataAcquired.get_day_k()["收盘"]
		return price[price.shape[0] - 1]

	def send_signal(self, maximumPrice) -> int:
		if (self.get_closing_price_today() > maximumPrice): # at least 100 * maximumPrice RMB to buy in
			return int(-maximumPrice)

		# falling trend
		if (self._MADay[5][-1] < self._MADay[60][-1]) or (self._MAWeek[5][-1] < self._MAWeek[60][-1]):
			return self.EMPTY

		# downturn of trend
		if (self._derivativeTodayDay[5] < 0 and self._derivativeTodayDay[20] < 0 and self._MADay[5][-1] < self._MADay[20][-1])\
		  or (self._derivativeTodayWeek[5] < 0 and self._derivativeTodayWeek[20] < 0 and self._MAWeek[5][-1] < self._MAWeek[20][-1]):
			return self.SELL

		if (self._derivativeTodayWeek[20] <= 0 and self._derivativeTodayMonth[20] <= 0)\
		  or (self._derivativeTodayDay[20] <= 0 and self._derivativeTodayWeek[20] <= 0):
			return self.WAIT
		elif (self._derivativeTodayDay[20] > 0 and self._derivativeTodayWeek[20] > 0 and self._derivativeTodayMonth[20] <= 0):
			# potential "terminal lucidity"
			if(self.get_closing_price_today() < 1.0 * min(self._lastMaximumDayMA5, self._lastMaximumWeekMA5)):
				return self.WAIT
			return self.RISING_SHORT
		elif (self._derivativeTodayWeek[20] > 0 and self._derivativeTodayMonth[20] > 0):
			# potential "terminal lucidity"
			if(self.get_closing_price_today() < 1.0 * min(self._lastMaximumWeekMA5, self._lastMaximumMonthMA5)):
				return self.WAIT
			return self.RISING_LONG
		# Noob, let's start with simple trends
		else:
			return self.WAIT

	def plot_MA_and_K(self, period):
		data = self.get_closing_price_history(period)
		MA = self.get_moving_average(period)
		if period in self.PeriodAlias[0]:
			period = "Day "
		elif period in self.PeriodAlias[1]:
			period = "Week "
		else:
			period = "Month "

		fig, ax = plt.subplots()
		windows = MA.keys()
		ax.plot(data, label = period + "K") #TODO: remove skipped date_time
		for window in windows:
			ax.plot(data.index[window - 1:], MA[window], label = "MA: " + str(window))
		plt.legend()
		plt.show()
		plt.close()


if __name__ == "__main__":
	df = pd.read_csv('stock_codes/CSI300_component_codes.csv', dtype = {0: str})
	header = df.columns[0]
	# 股票代码
	codes = df[header]

	signals = []
	urls = []
	size = len(codes)
	i = 1
	for code in codes:
		print(f"{i}/{size} 正在分析 {code} 的k线数据......")
		# read K-line data TODO: slicing the date using PANDAS
		dataAcquisitor = DataAcquisitor(code, 0, 0, False, 1, inDir = "stock_price_data")
		dataAnalyzer = DataAnalyzer(dataAcquisitor)
		if dataAnalyzer.get_data_acquired().get_code() == "000800":
			print("高点：", dataAnalyzer._lastMaximumDayMA5)
			dataAnalyzer.plot_MA_and_K(0)
			dataAnalyzer.plot_MA_and_K(1)
			dataAnalyzer.plot_MA_and_K(2)
		signals.append(dataAnalyzer.send_signal(60))
		urls.append(dataAnalyzer.get_data_acquired().get_quotation_url())
		i += 1
	signals = np.array(signals)
	print(len(signals[np.where(signals>0)]))
	df = pd.DataFrame({"股票代码": codes, "购买信号": signals, "行情地址": urls, "备注": ['' for i in range(len(codes))]})
	df.to_csv(f"signals.csv", encoding="utf-8-sig", index=None)

