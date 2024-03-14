import pandas as pd
import time
from data_acquisitor import DataAcquisitor


def acquire_and_save_stock_data(code: str, startDate: str, endDate: str, outDir: str):
	print(f"正在获取 {code} 从 {startDate} 到 {endDate} 的 k线数据......")
	# 根据股票代码、开始日期、结束日期获取指定股票代码指定日期区间的k线数据
	dataAcquisitor = DataAcquisitor(code, startDate, endDate, False, 0, outDir = outDir)
	# 保存k线数据到表格里面
	print(f"股票代码：{code} 的 k线数据已保存到指定目录 {outDir} 下的csv 文件中")
	dataAcquisitor.save_to_csv()

def acquire_and_save_stock_data_multiprocess(param):
	try:
		acquire_and_save_stock_data(*param)
		time.sleep(3)
		return 0
	except:
		time.sleep(3)
		return 1

def run_data_acquisitor(nproc: int, codes: list[str], startDate: str, endDate: str, outDir: str):
	size = len(codes)
	with Pool(nproc) as pool:
		result = list(tqdm(pool.imap(acquire_and_save_stock_data_multiprocess,
					  zip(codes, itertools.repeat(startDate), itertools.repeat(endDate), itertools.repeat(outDir))),
					  total = size))
		pool.close()

if __name__ == "__main__":
	from multiprocessing import Pool
	nproc = 10
	import itertools
	from tqdm.auto import tqdm

	# 开始日期
	startDate = "20180621"
	# 结束日期
	endDate   = pd.to_datetime("today").strftime("%Y%m%d")
	# 输出路径
	outDir    = "stock_price_data"

	# 股票代码
	df = pd.read_csv('stock_codes/CSI300_component_codes_exBFRE_exSTAR.csv', dtype = {0: str})
	header = df.columns[0]
	codes = df[header]

	print("下载沪深300成分股......")
	run_data_acquisitor(nproc, codes, startDate, endDate, outDir)


	# 股票代码
	df = pd.read_csv('stock_codes/CSI500_component_codes_exBFRE_exSTAR.csv', dtype = {0: str})
	header = df.columns[0]
	codes = df[header]

	print("下载中证500成分股......")
	run_data_acquisitor(nproc, codes, startDate, endDate, outDir)
