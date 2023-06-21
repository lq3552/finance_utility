import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from DataAcquisitor import DataAcquisitor

class DataAnalyzer(object):
	'''
	class-level (static) members
	'''
	EMPTY        = -2
	SELL         = -1
	WAIT         = 0
	RISING_SHORT = 1
	RISING_LONG  = 2

	def __init__(self, dataAcquired: DataAcquisitor):
		self.dataAcquired = dataAcquired
		self.MADay = {5:    self.compute_moving_average(0, 5),
					  10:   self.compute_moving_average(0, 10),
					  20:   self.compute_moving_average(0, 20),
					  60:   self.compute_moving_average(0, 60)}
		self.MAWeek = {5:   self.compute_moving_average(1, 5),
					   10:  self.compute_moving_average(1, 10),
					   20:  self.compute_moving_average(1, 20),
					   60:  self.compute_moving_average(1, 60)}
		self.MAMonth = {5:  self.compute_moving_average(2, 5),
					    10: self.compute_moving_average(2, 10),
					    20: self.compute_moving_average(2, 20)}
		self.derivativeTodayDay   = {5:  self.compute_derivative_today(0, 5),
									 20: self.compute_derivative_today(0, 20),
									 60: self.compute_derivative_today(0, 60)}
		self.derivativeTodayWeek  = {5:  self.compute_derivative_today(1, 5),
									 20: self.compute_derivative_today(1, 20),
									 60: self.compute_derivative_today(1, 60)}
		self.derivativeTodayMonth = {20: self.compute_derivative_today(2, 20)}

	def compute_moving_average(self, period: int, window: int): # for now I just assume we have enough data, otherwise simply skip
		if period == 0:
			data = self.dataAcquired.dayK["收盘"]
		elif period == 1:
			data = self.dataAcquired.weekK["收盘"]
		else:
			data = self.dataAcquired.monthK["收盘"]

		if len(data) < window: # not enough data, should only happen to Month-K
			return np.zeros(1)

		try:
			movingAverages = np.convolve(data, np.ones(window) / window, mode = "valid")
			return movingAverages
		except:
			return np.zeros(1)

	def compute_derivative_today(self, period: int, window: int, stencil: int = 2):
		'''
		param:
			period: day - 0, week - 1 or month - 2
		'''
		if period == 0:
			MA   = self.MADay[window]
		elif period == 1:
			MA   = self.MAWeek[window]
		else:
			MA   = self.MAMonth[window]
		try:
			return (MA[-1] - MA[-1 - stencil]) / stencil
		except:
			return 0

	def get_historical_maximum_closest_to_today(self, period: int):
		'''
		param:
			period: day - 0, week - 1 or month - 2
		'''
		return 0

	def get_closing_price_today(self):
		price = self.dataAcquired.dayK["收盘"]
		return price[price.shape[0] - 1]

	def send_signal(self, maximumPrice):
		if (self.get_closing_price_today() > maximumPrice): # at least 100 * maximumPrice RMB to buy in
			return self.WAIT

		# falling trend
		if (self.MADay[5][-1] < self.MADay[60][-1]) or (self.MAWeek[5][-1] < self.MAWeek[60][-1]):
			return self.EMPTY

		# downturn of trend
		if (self.derivativeTodayDay[5] < 0 and self.derivativeTodayDay[20] < 0 and self.MADay[5][-1] < self.MADay[20][-1])\
		  or (self.derivativeTodayWeek[5] < 0 and self.derivativeTodayWeek[20] < 0 and self.MAWeek[5][-1] < self.MAWeek[20][-1]):
			return self.SELL

		if (self.derivativeTodayWeek[20] <= 0 and self.derivativeTodayMonth[20] <= 0)\
		  or (self.derivativeTodayDay[20] <= 0 and self.derivativeTodayWeek[20] <= 0):
			return self.WAIT
		elif (self.derivativeTodayDay[20] > 0 and self.derivativeTodayWeek[20] > 0 and self.derivativeTodayMonth[20] <= 0):
			return self.RISING_SHORT
		elif (self.derivativeTodayWeek[20] > 0 and self.derivativeTodayMonth[20] > 0):
			return self.RISING_LONG
		else:
			return self.WAIT

	def plot_MA_and_K(self, period: int):
		if period == 0:
			data = self.dataAcquired.dayK["收盘"]
			MA   = self.MADay
			period = "Day "
		elif period == 1:
			data = self.dataAcquired.weekK["收盘"]
			MA   = self.MAWeek
			period = "Week "
		else:
			data = self.dataAcquired.monthK["收盘"]
			MA   = self.MAMonth
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
	codes = df[header] #["002230"] 

	signals = []
	size = len(codes)
	i = 1
	for code in codes:
		print(f"{i}/{size} 正在分析 {code} 的k线数据......")
		# read K-line data TODO: slicing the date using PANDAS
		dataAcquisitor = DataAcquisitor(code, 0, 0, False, 1, inDir = "stock_price_data")
		dataAnalyzer = DataAnalyzer(dataAcquisitor)
		if dataAcquisitor.code == "000063":
			dataAnalyzer.plot_MA_and_K(0)
			dataAnalyzer.plot_MA_and_K(1)
			dataAnalyzer.plot_MA_and_K(2)
		signal = dataAnalyzer.send_signal(60)
		signals.append(signal)
		i += 1
	signals = np.array(signals)
	print(len(signals[np.where(signals>0)]))
	df = pd.DataFrame({"股票代码": codes, "购买信号": signals})
	df.to_csv(f"signals.csv", encoding="utf-8-sig", dtype = {0: str}, index=None)

