import pandas as pd
from bond.bondETF_data_acquisitor import BondETFDataAcquisitor
from bond.bondETF_data_analyzer import BondETFDataAnalyzer


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
	codes = ["511090", "511260", "511010"]
	names = ["30年国债ETF", "10年国债ETF", "5年国债ETF"]
	# 久期（暂时为单一偿还期限）
	durations = ["30Y", "10Y", "5Y"]
	benchDurations = [["7Y", "10Y"], ["30Y"], ["30Y"]]

	BondETFDataAnalyzer.set_yield_curves(yieldCurves)
	for code, name, duration, benchDuration  in zip(codes, names, durations, benchDurations):
		print(f"正在分析{code}-{name}......")
		analyze_bondETF_data(code, startDate, endDate, inDir, duration, benchDuration)
