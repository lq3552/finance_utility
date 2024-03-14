import os
import numpy as np
import pandas as pd
import pandas_market_calendars as pm_calendar
from security_tools.stock_trend import DataAcquisitor
from security_tools.stock_trend import DataAnalyzer

def analyze_stock_data(code: str, startDate: str, endDate: str, inDir: str, priceLimit: np.float64):
	dataAcquisitor = DataAcquisitor(code, startDate, endDate, 1, inDir = inDir)
	dataAnalyzer = DataAnalyzer(dataAcquisitor)
	signal = dataAnalyzer.send_signal(priceLimit)
	url   = dataAnalyzer.get_data_acquired().get_quotation_url()
	return signal, url

def analyze_stock_data_multiprocess(param):
	return analyze_stock_data(*param)

def run_data_analyzer(nproc: int, codes: list[str], names: list[str], startDate: str, endDate: str, inDir: str, outDir: str, outPrefix: str, priceLimit: np.float64):
	size = len(codes)
	with Pool(nproc) as pool:
		signals, urls = zip(*tqdm(pool.imap(analyze_stock_data_multiprocess,
							zip(codes, itertools.repeat(startDate), itertools.repeat(endDate), itertools.repeat(inDir), itertools.repeat(priceLimit))),
							total = size))
		marketCalendar = pm_calendar.get_calendar('XSHG').schedule(start_date = startDate, end_date = endDate)
		endDateOld = pd.to_datetime(endDate) - pd.Timedelta(days=1)
		while not endDateOld in marketCalendar.index:
			if os.path.exists(f"{outDir}/{outPrefix}_{endDateOld.strftime('%Y%m%d')}.csv"):
				break
			endDateOld = endDateOld - pd.Timedelta(days=1)
		endDateOld = endDateOld.strftime("%Y%m%d")
		signalsOld, _ = zip(*tqdm(pool.imap(analyze_stock_data_multiprocess,
							zip(codes, itertools.repeat(startDate), itertools.repeat(endDateOld), itertools.repeat(inDir), itertools.repeat(priceLimit))),
							total = size))
		pool.close()

	print(f"保存购买信号......")
	df = pd.DataFrame({"股票简称":names.values, "行情地址": urls, "购买信号": signals, "上期信号": signalsOld, 
					   "上期备注": ['' for i in range(len(codes))], "备注": ['' for i in range(len(codes))]},
					   index = pd.Index(codes, name = "股票代码"))
	df.sort_values(by = ["购买信号","上期信号", "股票代码"], axis = 0, ascending = False, inplace = True) # by = [col2, col1] means sort col1 first, then col2
	try: 
		dfOld = pd.read_csv(f"{outDir}/{outPrefix}_{endDateOld}.csv", dtype = {"股票代码": str, "备注": str})
		dfOld.set_index("股票代码", inplace=True)
		df["上期备注"] = dfOld["备注"]
	except:
		print("You must be too lazy to analyze stock price data every business day :(")
	finally:
		df.to_csv(f"{outDir}/{outPrefix}_{endDate}.csv")

if __name__ == "__main__":
	from multiprocessing import Pool
	nproc = 10
	import itertools
	from tqdm.auto import tqdm

	# 开始日期
	startDate = "20180621"
	# 结束日期
	endDate   = pd.to_datetime("today").strftime("%Y%m%d")
	# 输入路径
	inDir     = "stock_price_data"
	# 保存路径
	signalsDir = "long_short_signals"
	signalsPrefix = "signalsCSI300"
	# 价格限制
	priceLimit = 200.0

	# 股票代码
	df = pd.read_csv('stock_codes/CSI300_component_codes_exBFRE_exSTAR.csv', dtype = {0: str})
	headerCode = df.columns[0]
	headerName = df.columns[1]
	codes = df[headerCode]
	names = df[headerName]

	print(f"正在分析沪深300成分股的k线数据......")
	outDir = signalsDir
	outPrefix = signalsPrefix
	size = len(codes)
	run_data_analyzer(nproc, codes, names, startDate, endDate, inDir, signalsDir, signalsPrefix, priceLimit)

	'''
	# example candlestick plot
	dataAcquisitor = DataAcquisitor("000157", startDate, endDate, False, 1, inDir = inDir)
	dataAnalyzer = DataAnalyzer(dataAcquisitor)
	dataAnalyzer.plot_MA_and_K("day")
	dataAnalyzer.plot_MA_and_K("week")
	dataAnalyzer.plot_MA_and_K("month")
	'''

	# 保存路径
	signalsPrefix = "signalsCSI500"
	# 股票代码
	df = pd.read_csv('stock_codes/CSI500_component_codes_exBFRE_exSTAR.csv', dtype = {0: str})
	headerCode = df.columns[0]
	headerName = df.columns[1]
	codes = df[headerCode]
	names = df[headerName]

	print(f"正在分析中证500成分股的k线数据......")
	run_data_analyzer(nproc, codes, names, startDate, endDate, inDir, signalsDir, signalsPrefix, priceLimit)
