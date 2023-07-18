import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import pandas_market_calendars as pm_calendar
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
	RISING_LONG  = 2
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
		self._MADay   = {3: self.compute_moving_average(0, 3),
						 5: self.compute_moving_average(0, 5),
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
		self._MAHour =  {3: self.compute_moving_average(3, 3),
					     5: self.compute_moving_average(3, 5),
					    20: self.compute_moving_average(3, 20),
					    60: self.compute_moving_average(3, 60)}
		self._smoothedDayMA5   = self.compute_smoothed_MA5(0, 11, deriv = 0)
		self._smoothedWeekMA5  = self.compute_smoothed_MA5(1, 11, deriv = 0)
		self._smoothedMonthMA5 = self.compute_smoothed_MA5(2, 11, deriv = 0)
		self._smoothedHourMA5  = self.compute_smoothed_MA5(3, 11, deriv = 0)
        # smoothed derivatives is used to find local extrema
		self._smoothedDerivativeDayMA5   = self.compute_smoothed_MA5(0, 11, deriv = 1)
		self._smoothedDerivativeWeekMA5  = self.compute_smoothed_MA5(1, 11, deriv = 1)
		self._smoothedDerivativeMonthMA5 = self.compute_smoothed_MA5(2, 11, deriv = 1)
		self._smoothedDerivativeHourMA5  = self.compute_smoothed_MA5(3, 11, deriv = 1)
		self._lastMaximumDayMA5   = self.compute_historical_maximum_closest_to_today(0)
		self._lastMaximumWeekMA5  = self.compute_historical_maximum_closest_to_today(1)
		self._lastMaximumMonthMA5 = self.compute_historical_maximum_closest_to_today(2)
		self._lastMaximumHourMA5  = self.compute_historical_maximum_closest_to_today(3)
        # simply approximate derivatives f today's trends by finite difference of MAs
		self._derivativeTodayDay   = {3: self.compute_derivative_today(0, 3, stencil = 2),
									  5: self.compute_derivative_today(0, 5, stencil = 2),
									 20: self.compute_derivative_today(0, 20, stencil = 2),
									 60: self.compute_derivative_today(0, 60, stencil = 2)}
		self._derivativeTodayWeek  = {5: self.compute_derivative_today(1, 5, stencil = 1),
									 20: self.compute_derivative_today(1, 20, stencil = 1),
									 60: self.compute_derivative_today(1, 60, stencil = 1)}
		self._derivativeTodayMonth = {20: self.compute_derivative_today(2, 20, stencil = 1)}
		self._derivativeTodayHour  = {3: self.compute_derivative_today(3, 3, stencil = 2),
									 20: self.compute_derivative_today(3, 20, stencil = 2),
									 60: self.compute_derivative_today(3, 60, stencil = 2)}

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

	def get_derivative_today(self, period):
		if period in self.PeriodAlias[0]:
			return self._derivativeTodayDay
		elif period in self.PeriodAlias[1]:
			return self._derivativeTodayWeek
		elif period in self.PeriodAlias[2]:
			return self._derivativeTodayMonth
		else:
			return self._derivativeTodayHour

	def compute_derivative_today(self, period, window: int, stencil: int = 2) -> np.float64:
		'''
		param:
			period: day - 0, week - 1, month - 2, hour - 3
		'''
		MA = self.get_moving_average(period)[window]
		try:
			return np.round((MA[-1] - MA[-1 - stencil]) / stencil, 2)
		except:
			return 0.0

	def get_historical_maximum_closest_to_today(self, period) -> np.float32:
		if period in self.PeriodAlias[0]:
			return self._lastMaximumDayMA5
		elif period in self.PeriodAlias[1]:
			return self._lastMaximumWeekMA5
		elif period in self.PeriodAlias[2]:
			return self._lastMaximumMonthMA5
		else:
			return self._lastMaximumHourMA5

	def compute_historical_maximum_closest_to_today(self, period) -> np.float32:
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

	def get_closing_price_today(self):
		price = self.get_closing_price_history(0)
		return price[price.shape[0] - 1]

	def send_signal(self, maximumPrice) -> int:

		priceClosing = self.get_closing_price_today()

		if (priceClosing > maximumPrice): # at least 100 * maximumPrice RMB to buy in
			return int(-maximumPrice)

		### short term
		if self._derivativeTodayDay[20] >= 0 and self._derivativeTodayWeek[20] >= 0 and self._derivativeTodayMonth[20] < 0:
			# potential "terminal lucidity"
			# if(priceClosing < 0.94 * self._lastMaximumDayMA5):
				# return self.WAIT
			# falling trend
			if priceClosing < self._MAHour[60][-1]:
				if self._derivativeTodayHour[3] > 0:
					return self.WAIT
				else:
					return self.EMPTY
			# downturn of trend
			if self._derivativeTodayHour[3] < 0 and self._derivativeTodayHour[20] < 0 and self._MAHour[3][-1] < self._MAHour[20][-1]:
				return self.SELL
			return self.RISING_SHORT
		### long term
		elif (self._derivativeTodayWeek[20] >= 0 and self._derivativeTodayMonth[20] >= 0):
			# potential "terminal lucidity"
			# if(priceClosing < 0.98 * min(self._lastMaximumWeekMA5, self._lastMaximumMonthMA5)):
				# if priceClosing >= 0.94 * self._lastMaximumDayMA5:
					# return self.RISING_SHORT
				# return self.WAIT
			# falling trend
			if priceClosing < self._MADay[60][-1]:
				if self._derivativeTodayDay[3] > 0:
					return self.WAIT
				else:
					return self.EMPTY
			# downturn of trend
			if self._derivativeTodayDay[3] < 0 and self._derivativeTodayDay[20] < 0 and self._MADay[3][-1] < self._MADay[20][-1]:
				return self.SELL
			return self.RISING_LONG
		# Noob, let's start with simple trends
		else:
			return self.WAIT

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


def analyze_stock_data(code: str, startDate: str, endDate: str, inDir: str):
	dataAcquisitor = DataAcquisitor(code, startDate, endDate, False, 1, inDir = inDir)
	dataAnalyzer = DataAnalyzer(dataAcquisitor)
	signal = dataAnalyzer.send_signal(60)
	url   = dataAnalyzer.get_data_acquired().get_quotation_url()
	return signal, url

def analyze_stock_data_multiprocess(param):
	return analyze_stock_data(*param)


if __name__ == "__main__":
	from multiprocessing import Pool
	nproc = 8
	import itertools
	from tqdm.auto import tqdm

	df = pd.read_csv('stock_codes/CSI300_component_codes.csv', dtype = {0: str})
	headerCode = df.columns[0]
	headerName = df.columns[1]
	# 股票代码
	codes = df[headerCode]
	names = df[headerName]
	# 开始日期
	startDate = "20180621"
	# 结束日期
	endDate   = pd.to_datetime("today").strftime("%Y%m%d")
	# 输入路径
	inDir     = "stock_price_data"

	size = len(codes)
	with Pool(nproc) as pool:
		print(f"正在分析沪深300成分股的k线数据......")
		signals, urls = zip(*tqdm(pool.imap(analyze_stock_data_multiprocess,
							zip(codes, itertools.repeat(startDate), itertools.repeat(endDate), itertools.repeat(inDir))),
							total = size))
		marketCalendar = pm_calendar.get_calendar('XSHG').schedule(start_date = startDate, end_date = endDate)
		endDateOld = pd.to_datetime(endDate) - pd.Timedelta(days=1)
		while not endDateOld in marketCalendar.index:
			endDateOld = endDateOld - pd.Timedelta(days=1)
		endDateOld = endDateOld.strftime("%Y%m%d")
		signalsOld, _ = zip(*tqdm(pool.imap(analyze_stock_data_multiprocess,
							zip(codes, itertools.repeat(startDate), itertools.repeat(endDateOld), itertools.repeat(inDir))),
							total = size))
		pool.close()

	print(f"保存购买信号......")
	signalsDir = "long_short_signals"
	df = pd.DataFrame({"股票简称":names.values, "行情地址": urls, "购买信号": signals, "上期信号": signalsOld, 
					   "上期备注": ['' for i in range(len(codes))], "备注": ['' for i in range(len(codes))]},
					   index = pd.Index(codes.astype(int), name = "股票代码"))
	df.sort_values(by = ["购买信号","上期信号", "股票代码"], axis = 0, ascending = False, inplace = True) # by = [col2, col1] means sort col1 first, then col2
	try: 
		dfOld = pd.read_csv(f"{signalsDir}/signals_{endDateOld}.csv", index_col = 0, dtype = {"备注": str})
		df["上期备注"] = dfOld["备注"]
	except:
		print("You must be too lazy to analyze stock price data every business day :(")
	finally:
		df.to_csv(f"{signalsDir}/signals_{endDate}.csv")

	'''
	# example candlestick plot
	dataAcquisitor = DataAcquisitor("000157", startDate, endDate, False, 1, inDir = inDir)
	dataAnalyzer = DataAnalyzer(dataAcquisitor)
	dataAnalyzer.plot_MA_and_K("day")
	dataAnalyzer.plot_MA_and_K("week")
	dataAnalyzer.plot_MA_and_K("month")
	'''
