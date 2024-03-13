import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from BondETFDataAcquisitor import BondETFDataAcquisitor


class BondETFDataAnalyzer(object):
	'''
	Information extractor and analyzer based on the stock data
	'''

	def __init__(self, dataAcquired: BondETFDataAcquisitor, yieldCurves: str, duration: str, benchDuration):
		'''
		param:
			dataAcquired: BondETFDataAcquisitor containing the stock data
			duration: duration of bond ETF
			benchDuration: a list of benchmark duration(s)
		'''
		self._dataAcquired  = dataAcquired
		self._duration      = duration
		self._benchDuration = benchDuration
		self._yieldCurves   = self._set_yield_curves(yieldCurves)
		self._closingPrices = self.get_closing_price_history()
		self._df            = self._closingPrices.join(self._yieldCurves)
		for d in benchDuration:
			sbd = "Spread_" + d
			self._df[sbd] = self._df["Yield_" + duration] - self._df["Yield_" + d]
			self._df[sbd] = (self._df[sbd] - self._df[sbd].min()) / (self._df[sbd].max() - self._df[sbd].min())
		yd = "Yield_"+ duration
		self._df[yd + "_scaled"] = (self._df[yd] - self._df[yd].min()) / (self._df[yd].max() - self._df[yd].min())
		print(self._df)

	def get_data_acquired(self) -> BondETFDataAcquisitor :
		'''
		return BondETFDataAcquisitor that contains the stock trading data
		'''
		return self._dataAcquired

	def _set_yield_curves(self, yieldCurves) -> pd.Series:
		data = pd.read_csv(f"{yieldCurves}", parse_dates = [0], index_col = 0, dtype = np.float64).loc[:, [self._duration] + self._benchDuration]
		data.rename(columns = {self._duration: "Yield_" + self._duration}, inplace = True)
		for d in self._benchDuration:
			data.rename(columns = {d: "Yield_" + d}, inplace = True)
		return data
	
	def get_yield_curves(self) -> pd.DataFrame:
		return self._yieldCurves

	def get_closing_price_history(self) -> pd.DataFrame:
		'''
		param:
			period: day - 0, week - 1, month - 2, hour - 3
		'''
		return self._dataAcquired.get_day_k().loc[:, ["Close", "涨跌幅"]]

	def correlate_price_with_yield(self):
		ax = self._df.plot("Close", ["Spread_" + d for d in self._benchDuration], style = "--")
		arr = self._df["Close"].to_numpy(copy = True)
		for i in range(len(self._benchDuration)):
			d = self._benchDuration[i]
			qToday = self._df["Spread_" + d].iloc[-1]
			q80    = self._df["Spread_" + d].quantile(0.8)
			q20    = self._df["Spread_" + d].quantile(0.2)
			print(qToday)
			ax.plot(arr, [qToday for n in range(arr.size)] , "C" + str(i) + "-")
			ax.plot(arr, [q80    for n in range(arr.size)] , "C" + str(i) + "-.")
			ax.plot(arr, [q20    for n in range(arr.size)] , "C" + str(i) + "-.")
		ax.set_ylabel("Quantity")
		ax.set_xlabel("Close")
		plt.show()
#		ax = self._df.plot("Spread", "Close", xlabel = "Spread", ylabel = "Close")
#		plt.show()


def analyze_bondETF_data(code: str, startDate: str, endDate: str, inDir: str, yieldCurves: str, duration: str, benchDuration: str):
	print(inDir)
	dataAcquisitor = BondETFDataAcquisitor(code, startDate, endDate, False, 1, inDir)
	dataAnalyzer = BondETFDataAnalyzer(dataAcquisitor, yieldCurves, duration, benchDuration)
	dataAnalyzer.correlate_price_with_yield()
	url   = dataAnalyzer.get_data_acquired().get_quotation_url()
	return url


if __name__ == "__main__":
	from multiprocessing import Pool
	nproc = 10
	import itertools
	from tqdm.auto import tqdm

	# 开始日期
	startDate = "20180621"
	# 结束日期
	endDate   = pd.to_datetime("today").strftime("%Y%m%d")
	# 输入
	inDir       = "bondETF_price_data/"
	yieldCurves = "yield_curves/CGBYieldCurve.csv"

	# ETF代码
	code = "511090"
	name = "30年国债ETF"
	# 久期（暂时为单一偿还期限）
	duration = "30Y"
	benchDuration = ["3Y", "5Y", "7Y", "10Y"]

	print(f"正在分析{code}-{name}......")
	analyze_bondETF_data(code, startDate, endDate, inDir, yieldCurves, duration, benchDuration)
