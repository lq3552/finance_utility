import numpy as np
from scipy.stats import kendalltau
import matplotlib.pyplot as plt
import pandas as pd
from BondETFDataAcquisitor import BondETFDataAcquisitor


class BondETFDataAnalyzer(object):
	'''
	Information extractor and analyzer based on the stock data
	'''
	_yieldCurves = pd.DataFrame()

	def __init__(self, dataAcquired: BondETFDataAcquisitor, duration: str, benchDuration: list[str], yieldCurves: str = None):
		'''
		param:
			dataAcquired: BondETFDataAcquisitor containing the stock data
			duration: duration of bond ETF
			benchDuration: a list of benchmark duration(s)
			yieldCurves: path to yield curve data
		'''
		print(type(benchDuration))
		self._dataAcquired  = dataAcquired
		self._duration      = duration
		self._benchDuration = benchDuration

		if self._yieldCurves.empty:
			self.set_yield_curves(yieldCurves)
		self._closingPrices = self.get_closing_price_history()
		self._df = self._closingPrices.join(self._yieldCurves[[duration] + benchDuration])
		print(self._df)
		for d in benchDuration:
			sd = "Spread_" + d
			self._df[sd] = self._df[duration] - self._df[d]
			self._df[sd] = (self._df[sd] - self._df[sd].min()) / (self._df[sd].max() - self._df[sd].min())
		self._df[duration + "_scaled"] = (self._df[duration] - self._df[duration].min()) / (self._df[duration].max() - self._df[duration].min())
		print(self._df)

	@classmethod
	def set_yield_curves(cls, yieldCurves) -> pd.Series:
		"""
		Setup yield curve data
		param:
			yieldCurves: path to yield curve data
		"""
		cls._yieldCurves = pd.read_csv(f"{yieldCurves}", parse_dates = [0], index_col = 0, dtype = np.float64)

	@classmethod
	def get_yield_curves(cls) -> pd.DataFrame:
		"""
		return:
			yield curve data as pandas DataFrame
		"""
		return cls._yieldCurves

	def get_data_acquired(self) -> BondETFDataAcquisitor :
		"""
		return:
			BondETFDataAcquisitor that contains the stock trading data
		"""
		return self._dataAcquired

	def get_closing_price_history(self) -> pd.DataFrame:
		"""
		return:
			day-K data with closing price and change as pandas DataFrame
		"""
		return self._dataAcquired.get_day_k().loc[:, ["Close", "涨跌幅"]]

	def correlate_price_with_yield(self):
#		ax = self._df.plot("Close", ["Spread_" + d for d in self._benchDuration], style = "--")
		fig, ax = plt.subplots()
		pArr = self._df["Close"].to_numpy(copy = True)
		pArr = pArr.astype(np.float64)
		pToday = pArr[-1]
		for i in range(len(self._benchDuration)):
			d = self._benchDuration[i]
			qArr = self._df["Spread_" + d].to_numpy(copy = True)
			ax.scatter(qArr, pArr, s = 16, color = "C" + str(i), label = d)
			print("CorrCoef_Kendall_" + d + " = ", kendalltau(qArr, pArr))
			qToday = qArr[-1]
			q80    = np.quantile(qArr, 0.8)
			q20    = np.quantile(qArr, 0.2)
			ax.plot([0, 1], [pToday, pToday], "k-", lw = 3)
			ax.plot([qToday, qToday], [pArr.min(), pArr.max()], "C" + str(i) + "-")
			ax.plot([q80, q80], [pArr.min(), pArr.max()], "C" + str(i) + "-.")
			ax.plot([q20, q20], [pArr.min(), pArr.max()], "C" + str(i) + "-.")
		ax.set_ylabel("Close")
		ax.set_xlabel("Spread")
		ax.legend()
		plt.show()
#		ax = self._df.plot("Spread", "Close", xlabel = "Spread", ylabel = "Close")
#		plt.show()


def analyze_bondETF_data(code: str, startDate: str, endDate: str, inDir: str,
		                 duration: str, benchDuration: list[str], yieldCurves: str = None):
	dataAcquisitor = BondETFDataAcquisitor(code, startDate, endDate, 1, inDir)
	dataAnalyzer = BondETFDataAnalyzer(dataAcquisitor, duration, benchDuration, yieldCurves = yieldCurves)
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
	benchDuration = ["7Y", "10Y"]

	print(f"正在分析{code}-{name}......")

	BondETFDataAnalyzer.set_yield_curves(yieldCurves)
	analyze_bondETF_data(code, startDate, endDate, inDir, duration, benchDuration)
